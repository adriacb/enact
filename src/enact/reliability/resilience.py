import time
import functools
from typing import Callable, Any, Optional, Type, Tuple
from dataclasses import dataclass

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd

class TimeoutError(Exception):
    """Raised when operation times out."""
    pass

class MaxRetriesExceeded(Exception):
    """Raised when max retry attempts exceeded."""
    pass

def with_timeout(timeout_seconds: float):
    """
    Decorator to add timeout to a function using threading.
    
    Args:
        timeout_seconds: Maximum execution time
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import threading
            
            # Mutable container for result/exception
            result = []
            
            def target():
                try:
                    val = func(*args, **kwargs)
                    result.append((True, val))
                except Exception as e:
                    result.append((False, e))
            
            t = threading.Thread(target=target)
            t.daemon = True
            t.start()
            t.join(timeout_seconds)
            
            if t.is_alive():
                raise TimeoutError(f"Operation timed out after {timeout_seconds}s")
            
            if not result:
                # Should trigger if join returned but thread hasn't finished (rare race)
                # or if thread died silently
                raise TimeoutError("Operation timed out or failed silently")
                
            success, value = result[0]
            if not success:
                raise value
            
            return value
        return wrapper
    return decorator

def with_retry(
    config: Optional[RetryConfig] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to add retry logic with exponential backoff.
    
    Args:
        config: Retry configuration
        exceptions: Tuple of exceptions to retry on
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = config.initial_delay
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        # Last attempt failed
                        raise MaxRetriesExceeded(
                            f"Failed after {config.max_attempts} attempts: {e}"
                        ) from e
                    
                    # Calculate backoff delay
                    if config.jitter:
                        import random
                        jitter_factor = random.uniform(0.5, 1.5)
                        actual_delay = min(delay * jitter_factor, config.max_delay)
                    else:
                        actual_delay = min(delay, config.max_delay)
                    
                    time.sleep(actual_delay)
                    
                    # Exponential backoff
                    delay *= config.exponential_base
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator

class ReliableToolProxy:
    """
    Proxy that wraps tools with timeout and retry logic.
    
    Provides resilient execution with automatic retries and timeouts.
    """
    
    def __init__(
        self,
        tool: Any,
        timeout_seconds: float = 30.0,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Args:
            tool: The tool to wrap
            timeout_seconds: Timeout for each execution
            retry_config: Retry configuration
        """
        self._tool = tool
        self._timeout = timeout_seconds
        self._retry_config = retry_config or RetryConfig()
    
    def __getattr__(self, name: str):
        """Intercept method calls and add resilience."""
        attr = getattr(self._tool, name)
        
        if not callable(attr):
            return attr
        
        @functools.wraps(attr)
        def resilient_wrapper(*args, **kwargs):
            # Apply retry logic
            @with_retry(self._retry_config)
            def with_retries():
                # Apply timeout
                @with_timeout(self._timeout)
                def with_timeout_wrapper():
                    return attr(*args, **kwargs)
                
                return with_timeout_wrapper()
            
            return with_retries()
        
        return resilient_wrapper
