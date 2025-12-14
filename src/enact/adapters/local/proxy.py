from typing import Any
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
            
            # Get active context
            from ...context import get_current_context
            ctx = get_current_context()
            
            request = GovernanceRequest(
                agent_id=self._agent_id,
                tool_name=self._target.__class__.__name__,
                function_name=name,
                arguments=combined_args,
                context=ctx,
                correlation_id=ctx.get("correlation_id")
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

        return governed_method

    def __call__(self, *args, **kwargs):
        """
        Allows the proxy to be called directly if the target is a function/callable.
        """
        if not callable(self._target):
            raise TypeError(f"The governed object {self._target!r} is not callable.")

        # Re-use logic for method interception but for direct call
        # Create request for the callable itself
        name = getattr(self._target, "__name__", "<callable>")
        
        # Get active context
        from ...context import get_current_context
        ctx = get_current_context()
        
        combined_args = {"args": args, "kwargs": kwargs}
            
        request = GovernanceRequest(
            agent_id=self._agent_id,
            tool_name=name, # Treating function name as tool name
            function_name=name,
            arguments=combined_args,
            context=ctx,
            correlation_id=ctx.get("correlation_id")
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
        
        return self._target(*final_args, **final_kwargs)

    def __repr__(self):
        return f"<ToolProxy for {self._target!r}>"
