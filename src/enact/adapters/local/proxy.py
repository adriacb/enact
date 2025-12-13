from typing import Any, Callable
from ...core.domain import GovernanceRequest
from ...core.interactors import GovernanceEngine

class ToolProxy:
    """
    A proxy wrapper for local Python objects that enforces governance policies.
    """
    def __init__(self, target: Any, engine: GovernanceEngine, agent_id: str = "default-agent"):
        self._target = target
        self._engine = engine
        self._agent_id = agent_id

    def __getattr__(self, name: str) -> Any:
        """
        Intercepts attribute access to wrap methods with governance logic.
        """
        attr = getattr(self._target, name)
        
        if not callable(attr):
            # For now, we only govern method calls, not property access
            return attr
        
        def governed_method(*args, **kwargs):
            # Construct the request
            # Note: We might need a better way to map *args to named arguments
            # for the policy to understand them fully. For now, passing raw args/kwargs.
            combined_args = {"args": args, "kwargs": kwargs}
            
            request = GovernanceRequest(
                agent_id=self._agent_id,
                tool_name=self._target.__class__.__name__,
                function_name=name,
                arguments=combined_args
            )
            
            decision = self._engine.evaluate(request)
            
            if not decision.allow:
                raise PermissionError(f"Governance violation: {decision.reason}")
            
            # Use modified arguments if provided, otherwise originals
            final_args = args
            final_kwargs = kwargs
            
            if decision.modified_arguments:
                final_args = decision.modified_arguments.get("args", args)
                final_kwargs = decision.modified_arguments.get("kwargs", kwargs)
            
            return attr(*final_args, **final_kwargs)
            
        return governed_method

    def __repr__(self):
        return f"<ToolProxy for {self._target!r}>"
