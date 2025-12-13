import pytest
from enact import InMemoryToolRegistry, Rule, RuleBasedPolicy, GovernanceRequest, GovernanceDecision, Policy

# Mock tool
class DatabaseTool:
    def query(self, sql):
        return f"Executing: {sql}"

# Mock policy
class ReadOnlyPolicy(Policy):
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        if "delete" in request.function_name.lower():
            return GovernanceDecision(allow=False, reason="Read-only mode")
        return GovernanceDecision(allow=True, reason="Allowed")

def test_register_and_get_tool():
    """Test basic tool registration and retrieval."""
    registry = InMemoryToolRegistry()
    db = DatabaseTool()
    
    registry.register_tool("database", db)
    
    # Any agent can access unrestricted tool
    retrieved = registry.get_tool("database", "agent1")
    assert retrieved is db

def test_tool_access_control_by_agent():
    """Test that tools can be restricted to specific agents."""
    registry = InMemoryToolRegistry()
    db = DatabaseTool()
    
    registry.register_tool("database", db, allowed_agents=["agent1", "agent2"])
    
    # Allowed agent
    assert registry.get_tool("database", "agent1") is db
    
    # Denied agent
    assert registry.get_tool("database", "agent3") is None

def test_agent_groups():
    """Test agent group functionality."""
    registry = InMemoryToolRegistry()
    db = DatabaseTool()
    
    # Create group
    registry.create_group("admins")
    registry.add_agent_to_group("alice", "admins")
    registry.add_agent_to_group("bob", "admins")
    
    # Register tool for group
    registry.register_tool("database", db, allowed_groups=["admins"])
    
    # Group members can access
    assert registry.get_tool("database", "alice") is db
    assert registry.get_tool("database", "bob") is db
    
    # Non-members cannot
    assert registry.get_tool("database", "charlie") is None

def test_policy_inheritance():
    """Test policy precedence: tool > agent > group."""
    registry = InMemoryToolRegistry()
    db = DatabaseTool()
    
    # Group policy
    group_policy = ReadOnlyPolicy()
    registry.create_group("viewers", policy=group_policy)
    registry.add_agent_to_group("agent1", "viewers")
    
    # Agent policy (overrides group)
    agent_policy = RuleBasedPolicy([
        Rule(tool="*", function="*", action="allow", reason="Agent override")
    ])
    registry.set_agent_policy("agent2", agent_policy)
    registry.add_agent_to_group("agent2", "viewers")
    
    # Tool policy (highest priority)
    tool_policy = RuleBasedPolicy([
        Rule(tool="*", function="*", action="deny", reason="Tool locked")
    ])
    registry.register_tool("database", db, policy=tool_policy)
    
    # Tool policy wins
    assert registry.get_policy_for_tool("database", "agent1") is tool_policy
    assert registry.get_policy_for_tool("database", "agent2") is tool_policy

def test_list_tools_for_agent():
    """Test listing accessible tools for an agent."""
    registry = InMemoryToolRegistry()
    
    registry.register_tool("public_tool", DatabaseTool())
    registry.register_tool("admin_tool", DatabaseTool(), allowed_agents=["admin"])
    
    registry.create_group("devs")
    registry.add_agent_to_group("dev1", "devs")
    registry.register_tool("dev_tool", DatabaseTool(), allowed_groups=["devs"])
    
    # Public tool visible to all
    assert "public_tool" in registry.list_tools_for_agent("anyone")
    
    # Admin tool only for admin
    admin_tools = registry.list_tools_for_agent("admin")
    assert "admin_tool" in admin_tools
    assert "public_tool" in admin_tools
    
    # Dev tools for group members
    dev_tools = registry.list_tools_for_agent("dev1")
    assert "dev_tool" in dev_tools
    assert "public_tool" in dev_tools
    assert "admin_tool" not in dev_tools

def test_unregister_tool():
    """Test tool removal."""
    registry = InMemoryToolRegistry()
    registry.register_tool("temp_tool", DatabaseTool())
    
    assert registry.get_tool("temp_tool", "agent1") is not None
    
    registry.unregister_tool("temp_tool")
    
    assert registry.get_tool("temp_tool", "agent1") is None
