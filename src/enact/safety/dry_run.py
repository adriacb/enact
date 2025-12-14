from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime

@dataclass
class DryRunResult:
    """Result of a dry-run execution."""
    tool_name: str
    function_name: str
    arguments: Dict[str, Any]
    timestamp: datetime
    would_execute: str
    estimated_impact: str = "Unknown"

class DryRunProxy:
    """
    Proxy that simulates tool execution without actually running it.
    
    Useful for testing governance policies and understanding what
    an agent would do without actually executing the actions.
    """
    
    def __init__(self, tool: Any, tool_name: str):
        """
        Args:
            tool: The actual tool to simulate
            tool_name: Name of the tool for logging
        """
        self._tool = tool
        self._tool_name = tool_name
        self._executions = []
    
    def __getattr__(self, name: str):
        """Intercept all method calls."""
        # Check if attribute exists on the real tool
        if not hasattr(self._tool, name):
            raise AttributeError(f"'{self._tool_name}' has no attribute '{name}'")
        
        def dry_run_wrapper(*args, **kwargs):
            """Simulate the function call."""
            result = DryRunResult(
                tool_name=self._tool_name,
                function_name=name,
                arguments={"args": args, "kwargs": kwargs},
                timestamp=datetime.now(),
                would_execute=f"{self._tool_name}.{name}({self._format_args(args, kwargs)})"
            )
            
            # Try to estimate impact
            result.estimated_impact = self._estimate_impact(name, args, kwargs)
            
            # Record the execution
            self._executions.append(result)
            
            return result
        
        return dry_run_wrapper
    
    def _format_args(self, args: tuple, kwargs: dict) -> str:
        """Format arguments for display."""
        parts = []
        
        if args:
            parts.extend([repr(arg) for arg in args])
        
        if kwargs:
            parts.extend([f"{k}={repr(v)}" for k, v in kwargs.items()])
        
        return ", ".join(parts)
    
    def _estimate_impact(self, function_name: str, args: tuple, kwargs: dict) -> str:
        """Estimate the impact of the function call."""
        # Simple heuristics for common operations
        lower_name = function_name.lower()
        
        if any(word in lower_name for word in ["delete", "remove", "drop"]):
            return "HIGH - Destructive operation"
        elif any(word in lower_name for word in ["create", "insert", "add", "update"]):
            return "MEDIUM - Mutating operation"
        elif any(word in lower_name for word in ["read", "get", "list", "query", "select"]):
            return "LOW - Read-only operation"
        else:
            return "UNKNOWN - Impact unclear"
    
    def get_executions(self) -> list:
        """Get all simulated executions."""
        return self._executions.copy()
    
    def clear_executions(self):
        """Clear execution history."""
        self._executions.clear()
