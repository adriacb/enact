import pytest
from enact import InMemoryToolRegistry

def test_tool_versioning_basic():
    """Test registering and retrieving multiple versions."""
    registry = InMemoryToolRegistry()
    
    # Version 1.0.0
    registry.register_tool("calculator", lambda: "v1", version="1.0.0")
    
    # Version 2.0.0
    registry.register_tool("calculator", lambda: "v2", version="2.0.0")
    
    # get_tool should return latest (v2)
    tool = registry.get_tool("calculator", "agent1")
    assert tool() == "v2"
    
    # get_tool_version 1.0.0
    v1 = registry.get_tool_version("calculator", "1.0.0", "agent1")
    assert v1() == "v1"
    
    # get_tool_version 2.0.0
    v2 = registry.get_tool_version("calculator", "2.0.0", "agent1")
    assert v2() == "v2"

def test_tool_version_overwrites():
    """Test that registering same version updates it."""
    registry = InMemoryToolRegistry()
    
    registry.register_tool("calc", lambda: "old", version="1.0")
    registry.register_tool("calc", lambda: "new", version="1.0")
    
    tool = registry.get_tool("calc", "agent1")
    assert tool() == "new"

def test_tool_version_access_control():
    """Test that access is checked for specific versions."""
    registry = InMemoryToolRegistry()
    
    # v1 is public
    registry.register_tool("secret", lambda: "v1", version="1.0")
    
    # v2 is restricted
    registry.register_tool("secret", lambda: "v2", version="2.0", allowed_agents=["admin"])
    
    # User 'guest' should see v1 but NOT v2
    assert registry.get_tool_version("secret", "1.0", "guest") is not None
    assert registry.get_tool_version("secret", "2.0", "guest") is None
    
    # User 'admin' should see both
    assert registry.get_tool_version("secret", "1.0", "admin") is not None
    assert registry.get_tool_version("secret", "2.0", "admin") is not None
