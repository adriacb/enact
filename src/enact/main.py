from typing import Any, Union
from .core.domain import Policy
from .core.interactors import GovernanceEngine
from .adapters.local.proxy import ToolProxy

def govern(
    tool: Any = None, 
    policy: Union[Policy, None] = None, 
    engine: Union[GovernanceEngine, None] = None,
    agent_id: str = "default-agent"
) -> Any:
    """
    Wraps a tool with a governance layer.
    Can be used as a function or a decorator.
    
    Args:
        tool: The tool to govern.
        policy: Optional policy (used if engine is not provided).
        engine: Existing GovernanceEngine to reuse.
        agent_id: The identity of the agent using this tool.
    """
    # 1. Resolve Engine
    if engine is None:
        engine = GovernanceEngine(policy=policy)
    
    # 2. Define wrapper logic
    def _wrap(target):
        return ToolProxy(target=target, engine=engine, agent_id=agent_id)

    # 3. Handle usage as decorator vs function
    if tool is None:
        return _wrap
    
    return _wrap(tool)
