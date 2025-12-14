from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Protocol
from ..core.domain import Policy

@dataclass
class AgentGroup:
    """Represents a group of agents with shared policies."""
    name: str
    policy: Optional[Policy] = None
    members: Set[str] = field(default_factory=set)

@dataclass
class ToolRegistration:
    """Represents a registered tool with its metadata."""
    name: str
    tool: Any
    policy: Optional[Policy] = None
    allowed_agents: Set[str] = field(default_factory=set)
    allowed_groups: Set[str] = field(default_factory=set)
    expires_at: Optional[datetime] = None

class ToolRegistry(Protocol):
    """
    Protocol for tool registries.
    Defines the interface for centralized tool and policy management.
    """
    
    def register_tool(
        self,
        name: str,
        tool: Any,
        policy: Optional[Policy] = None,
        allowed_agents: Optional[List[str]] = None,
        allowed_groups: Optional[List[str]] = None
    ) -> None:
        """Register a tool in the registry."""
        ...
    
    def unregister_tool(self, name: str) -> None:
        """Remove a tool from the registry."""
        ...
    
    def create_group(self, name: str, policy: Optional[Policy] = None) -> None:
        """Create an agent group with optional shared policy."""
        ...
    
    def add_agent_to_group(self, agent_id: str, group_name: str) -> None:
        """Add an agent to a group."""
        ...
    
    def set_agent_policy(self, agent_id: str, policy: Policy) -> None:
        """Set a policy specific to an agent."""
        ...
    
    def get_tool(self, name: str, agent_id: str) -> Optional[Any]:
        """Get a tool if the agent has access to it."""
        ...
    
    def get_policy_for_tool(self, tool_name: str, agent_id: str) -> Optional[Policy]:
        """Get the effective policy for a tool-agent combination."""
        ...
    
    def list_tools_for_agent(self, agent_id: str) -> List[str]:
        """List all tools accessible to an agent."""
        ...

class InMemoryToolRegistry:
    """
    In-memory implementation of the ToolRegistry protocol.
    
    Features:
    - Register tools with specific policies
    - Define agent groups with inherited policies
    - Query tools by agent, group, or policy
    - Policy inheritance: tool → agent → group
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolRegistration] = {}
        self.groups: Dict[str, AgentGroup] = {}
        self.agent_policies: Dict[str, Policy] = {}
    
    def register_tool(
        self,
        name: str,
        tool: Any,
        policy: Optional[Policy] = None,
        allowed_agents: Optional[List[str]] = None,
        allowed_groups: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> None:
        """
        Register a tool in the registry.
        
        Args:
            name: Unique tool identifier
            tool: The actual tool object
            policy: Tool-specific policy (highest priority)
            allowed_agents: List of agent IDs that can access this tool
            allowed_groups: List of group names that can access this tool
            expires_at: Optional expiration time for this registration
        """
        self.tools[name] = ToolRegistration(
            name=name,
            tool=tool,
            policy=policy,
            allowed_agents=set(allowed_agents or []),
            allowed_groups=set(allowed_groups or []),
            expires_at=expires_at
        )
    
    def unregister_tool(self, name: str) -> None:
        """Remove a tool from the registry."""
        if name in self.tools:
            del self.tools[name]
    
    def create_group(self, name: str, policy: Optional[Policy] = None) -> None:
        """
        Create an agent group with optional shared policy.
        
        Args:
            name: Group identifier
            policy: Policy that applies to all group members
        """
        self.groups[name] = AgentGroup(name=name, policy=policy)
    
    def add_agent_to_group(self, agent_id: str, group_name: str) -> None:
        """Add an agent to a group."""
        if group_name not in self.groups:
            raise ValueError(f"Group '{group_name}' does not exist")
        self.groups[group_name].members.add(agent_id)
    
    def set_agent_policy(self, agent_id: str, policy: Policy) -> None:
        """Set a policy specific to an agent."""
        self.agent_policies[agent_id] = policy
    
    def get_tool(self, name: str, agent_id: str) -> Optional[Any]:
        """
        Get a tool if the agent has access to it.
        
        Args:
            name: Tool name
            agent_id: Agent requesting the tool
            
        Returns:
            The tool object if accessible, None otherwise
        """
        if name not in self.tools:
            return None
        
        registration = self.tools[name]
        
        # Check expiration
        if registration.expires_at and datetime.now() > registration.expires_at:
            return None
        
        # If no restrictions, allow access
        if not registration.allowed_agents and not registration.allowed_groups:
            return registration.tool
        
        # Check direct agent access
        if registration.allowed_agents and agent_id in registration.allowed_agents:
            return registration.tool
        
        # Check group access
        if registration.allowed_groups:
            agent_groups = self._get_agent_groups(agent_id)
            if registration.allowed_groups.intersection(agent_groups):
                return registration.tool
        
        # Access denied
        return None
    
    def get_policy_for_tool(self, tool_name: str, agent_id: str) -> Optional[Policy]:
        """
        Get the effective policy for a tool-agent combination.
        
        Policy precedence (highest to lowest):
        1. Tool-specific policy
        2. Agent-specific policy
        3. Group policy
        4. None (allow all)
        """
        if tool_name not in self.tools:
            return None
        
        registration = self.tools[tool_name]
        
        # 1. Tool-specific policy
        if registration.policy:
            return registration.policy
        
        # 2. Agent-specific policy
        if agent_id in self.agent_policies:
            return self.agent_policies[agent_id]
        
        # 3. Group policy
        agent_groups = self._get_agent_groups(agent_id)
        for group_name in agent_groups:
            if self.groups[group_name].policy:
                return self.groups[group_name].policy
        
        return None
    
    def list_tools_for_agent(self, agent_id: str) -> List[str]:
        """List all tools accessible to an agent."""
        accessible_tools = []
        agent_groups = self._get_agent_groups(agent_id)
        
        for name, registration in self.tools.items():
            # If no restrictions, tool is accessible
            if not registration.allowed_agents and not registration.allowed_groups:
                accessible_tools.append(name)
                continue
            
            # Check direct access
            if agent_id in registration.allowed_agents:
                accessible_tools.append(name)
                continue
            
            # Check group access
            if registration.allowed_groups.intersection(agent_groups):
                accessible_tools.append(name)
        
        return accessible_tools
    
    def _get_agent_groups(self, agent_id: str) -> Set[str]:
        """Get all groups an agent belongs to."""
        return {
            group_name
            for group_name, group in self.groups.items()
            if agent_id in group.members
        }
