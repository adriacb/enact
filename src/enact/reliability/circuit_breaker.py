from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: int = 60   # Time before trying half-open

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by stopping requests to failing tools.
    States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        
        # Per-tool circuit state
        self.circuits: Dict[str, dict] = {}
    
    def _get_circuit(self, tool_name: str) -> dict:
        """Get or create circuit for tool."""
        if tool_name not in self.circuits:
            self.circuits[tool_name] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure_time": None,
            }
        return self.circuits[tool_name]
    
    def _should_attempt_reset(self, circuit: dict) -> bool:
        """Check if enough time has passed to try half-open."""
        if circuit["state"] != CircuitState.OPEN:
            return False
        
        if circuit["last_failure_time"] is None:
            return True
        
        elapsed = (datetime.now() - circuit["last_failure_time"]).total_seconds()
        return elapsed >= self.config.timeout_seconds
    
    def is_open(self, tool_name: str) -> bool:
        """Check if circuit is open (blocking requests)."""
        circuit = self._get_circuit(tool_name)
        
        # Try to move to half-open if timeout passed
        if self._should_attempt_reset(circuit):
            circuit["state"] = CircuitState.HALF_OPEN
            circuit["success_count"] = 0
        
        return circuit["state"] == CircuitState.OPEN
    
    def record_success(self, tool_name: str):
        """Record successful tool execution."""
        circuit = self._get_circuit(tool_name)
        
        if circuit["state"] == CircuitState.HALF_OPEN:
            circuit["success_count"] += 1
            
            # Close circuit if enough successes
            if circuit["success_count"] >= self.config.success_threshold:
                circuit["state"] = CircuitState.CLOSED
                circuit["failure_count"] = 0
                circuit["success_count"] = 0
        
        elif circuit["state"] == CircuitState.CLOSED:
            # Reset failure count on success
            circuit["failure_count"] = 0
    
    def record_failure(self, tool_name: str):
        """Record failed tool execution."""
        circuit = self._get_circuit(tool_name)
        circuit["last_failure_time"] = datetime.now()
        
        if circuit["state"] == CircuitState.HALF_OPEN:
            # Failure in half-open -> back to open
            circuit["state"] = CircuitState.OPEN
            circuit["success_count"] = 0
        
        elif circuit["state"] == CircuitState.CLOSED:
            circuit["failure_count"] += 1
            
            # Open circuit if threshold exceeded
            if circuit["failure_count"] >= self.config.failure_threshold:
                circuit["state"] = CircuitState.OPEN
    
    def get_state(self, tool_name: str) -> CircuitState:
        """Get current circuit state for tool."""
        circuit = self._get_circuit(tool_name)
        return circuit["state"]
    
    def reset(self, tool_name: str):
        """Manually reset circuit to closed state."""
        if tool_name in self.circuits:
            del self.circuits[tool_name]

class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass
