from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int  # Maximum tokens
    refill_rate: float  # Tokens per second
    tokens: float = field(init=False)
    last_refill: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.tokens = float(self.capacity)
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        
        # Add tokens based on refill rate
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Returns:
            True if tokens were consumed, False if rate limit exceeded
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_available_tokens(self) -> float:
        """Get current available tokens."""
        self._refill()
        return self.tokens

class RateLimiter:
    """
    Rate limiter for controlling tool access frequency.
    
    Uses token bucket algorithm to allow bursts while maintaining
    average rate limits.
    """
    
    def __init__(
        self,
        max_calls_per_minute: int = 60,
        burst_size: Optional[int] = None
    ):
        """
        Args:
            max_calls_per_minute: Maximum calls allowed per minute
            burst_size: Maximum burst size (defaults to max_calls_per_minute)
        """
        self.max_calls_per_minute = max_calls_per_minute
        self.burst_size = burst_size or max_calls_per_minute
        
        # Buckets per agent-tool combination
        self.buckets: Dict[str, TokenBucket] = {}
    
    def _get_key(self, agent_id: str, tool_name: str) -> str:
        """Generate key for agent-tool combination."""
        return f"{agent_id}:{tool_name}"
    
    def _get_bucket(self, agent_id: str, tool_name: str) -> TokenBucket:
        """Get or create token bucket for agent-tool."""
        key = self._get_key(agent_id, tool_name)
        
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(
                capacity=self.burst_size,
                refill_rate=self.max_calls_per_minute / 60.0  # per second
            )
        
        return self.buckets[key]
    
    def check_limit(self, agent_id: str, tool_name: str) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            agent_id: Agent making the request
            tool_name: Tool being accessed
            
        Returns:
            True if allowed, False if rate limit exceeded
        """
        bucket = self._get_bucket(agent_id, tool_name)
        return bucket.consume()
    
    def get_remaining(self, agent_id: str, tool_name: str) -> float:
        """Get remaining tokens for agent-tool."""
        bucket = self._get_bucket(agent_id, tool_name)
        return bucket.get_available_tokens()
    
    def reset(self, agent_id: str, tool_name: str):
        """Reset rate limit for agent-tool."""
        key = self._get_key(agent_id, tool_name)
        if key in self.buckets:
            del self.buckets[key]
