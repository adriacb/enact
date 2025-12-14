from dataclasses import dataclass
from typing import Any, Optional
from ..registry.tool_registry import ToolRegistry

@dataclass
class VersionInfo:
    """Version metadata."""
    version: str
    changelog: Optional[str] = None
    deprecated: bool = False

class ToolLifecycleManager:
    """
    Helper class to manage tool versions interactions.
    Use this to interact with the ToolRegistry for advanced lifecycle operations.
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def register_version(
        self, 
        name: str, 
        tool: Any, 
        version: str, 
        **kwargs
    ):
        """Register a specific version of a tool."""
        self.registry.register_tool(name, tool, version=version, **kwargs)

    def get_latest(self, name: str, agent_id: str) -> Any:
        return self.registry.get_tool(name, agent_id)

    def get_version(self, name: str, version: str, agent_id: str) -> Any:
        return self.registry.get_tool_version(name, version, agent_id)
