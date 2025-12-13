from typing import Any, Union
from .core.domain import Policy
from .core.interactors import GovernanceEngine
from .adapters.local.proxy import ToolProxy

def govern(tool: Any, policy: Union[Policy, None] = None, agent_id: str = "default-agent") -> Any:
    """
    Wraps a tool with a governance layer.
    
    Args:
        tool: The tool to govern. Can be a Python object or (in the future) an MCP client.
        policy: The policy to enforce. If None, an AllowAllPolicy is used.
        agent_id: The identity of the agent using this tool.
        
    Returns:
        A proxied version of the tool.
    """
    engine = GovernanceEngine(policy=policy)
    
    # Future expansion: Check if tool is an MCP client and use an MCP Adapter.
    # For now, we assume it's a local Python object.
    
    return ToolProxy(target=tool, engine=engine, agent_id=agent_id)
