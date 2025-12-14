from contextvars import ContextVar
from contextlib import contextmanager
from typing import Dict, Any, Generator, Optional

# Context variable to store governance metadata
_governance_context: ContextVar[Dict[str, Any]] = ContextVar("governance_context", default={})

@contextmanager
def governance_context(
    justification: Optional[str] = None,
    correlation_id: Optional[str] = None,
    **kwargs
) -> Generator[None, None, None]:
    """
    Context manager to set governance context for the current execution scope.
    
    Usage:
        with governance_context(justification="User asked for it"):
            tool.do_something()
    """
    current_context = _governance_context.get().copy()
    
    # Update context
    if justification:
        current_context["justification"] = justification
    if correlation_id:
        current_context["correlation_id"] = correlation_id
        
    # Add any other kwargs
    current_context.update(kwargs)
    
    token = _governance_context.set(current_context)
    try:
        yield
    finally:
        _governance_context.reset(token)

def get_current_context() -> Dict[str, Any]:
    """Get the current governance context."""
    return _governance_context.get()
