# Tool Registry Guide

The Tool Registry provides centralized management of tools with support for agent groups, access control, and policy inheritance.

## Overview

The Tool Registry allows you to:
- Register tools with access restrictions
- Organize agents into groups
- Define policies at tool, agent, or group level
- Query accessible tools for any agent

## Basic Usage

### Creating a Registry

```python
from enact import InMemoryToolRegistry

registry = InMemoryToolRegistry()
```

### Registering Tools

```python
# Public tool (no restrictions)
registry.register_tool("calculator", calculator_tool)

# Restricted to specific agents
registry.register_tool("admin_db", db_tool, allowed_agents=["admin", "superuser"])

# Restricted to agent groups
registry.register_tool("dev_api", api_tool, allowed_groups=["developers"])
```

### Agent Groups

```python
# Create a group
registry.create_group("developers")

# Add agents to the group
registry.add_agent_to_group("alice", "developers")
registry.add_agent_to_group("bob", "developers")

# Create group with shared policy
from enact import RuleBasedPolicy, Rule

dev_policy = RuleBasedPolicy([
    Rule(tool="*", function="delete.*", action="deny", reason="Devs can't delete")
])

registry.create_group("developers", policy=dev_policy)
```

## Access Control

### Getting Tools

```python
# Get tool for an agent (returns None if access denied)
tool = registry.get_tool("admin_db", "alice")

if tool:
    # Agent has access
    result = tool.query("SELECT * FROM users")
else:
    # Access denied
    print("Agent doesn't have access to this tool")
```

### Listing Accessible Tools

```python
# Get all tools accessible to an agent
tools = registry.list_tools_for_agent("alice")
print(f"Alice can access: {tools}")
```

## Policy Inheritance

Policies are evaluated in the following order (highest to lowest priority):

1. **Tool-specific policy** - Set when registering the tool
2. **Agent-specific policy** - Set for individual agents
3. **Group policy** - Inherited from agent's groups
4. **No policy** (allow all)

### Example

```python
# Group policy (lowest priority)
group_policy = RuleBasedPolicy([
    Rule(tool="*", function="*", action="allow", reason="Default allow")
])
registry.create_group("users", policy=group_policy)
registry.add_agent_to_group("alice", "users")

# Agent policy (overrides group)
agent_policy = RuleBasedPolicy([
    Rule(tool="database", function="delete.*", action="deny", reason="Alice can't delete")
])
registry.set_agent_policy("alice", agent_policy)

# Tool policy (highest priority - overrides everything)
tool_policy = RuleBasedPolicy([
    Rule(tool="*", function="*", action="deny", reason="Tool locked")
])
registry.register_tool("locked_db", db_tool, policy=tool_policy)

# Get effective policy for alice accessing locked_db
policy = registry.get_policy_for_tool("locked_db", "alice")
# Returns tool_policy (highest priority)
```

## Advanced Patterns

### Role-Based Access Control (RBAC)

```python
# Define roles as groups
registry.create_group("admins")
registry.create_group("developers")
registry.create_group("viewers")

# Assign tools to roles
registry.register_tool("admin_panel", admin_tool, allowed_groups=["admins"])
registry.register_tool("dev_console", console_tool, allowed_groups=["developers", "admins"])
registry.register_tool("dashboard", dashboard_tool, allowed_groups=["viewers", "developers", "admins"])

# Assign users to roles
registry.add_agent_to_group("alice", "admins")
registry.add_agent_to_group("bob", "developers")
registry.add_agent_to_group("charlie", "viewers")
```

### Dynamic Tool Registration

```python
def register_user_tools(registry, user_id, user_role):
    """Dynamically register tools based on user role."""
    
    # Everyone gets basic tools
    registry.register_tool(f"{user_id}_notes", NotesTool(user_id))
    
    # Role-specific tools
    if user_role == "admin":
        registry.register_tool(
            f"{user_id}_admin_panel",
            AdminPanel(),
            allowed_agents=[user_id]
        )
```

## Implementing Custom Registries

The `ToolRegistry` is a protocol, so you can implement your own:

```python
from enact.registry import ToolRegistry
import redis

class RedisToolRegistry:
    """Tool registry backed by Redis."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def register_tool(self, name, tool, policy=None, allowed_agents=None, allowed_groups=None):
        # Store in Redis
        self.redis.hset(f"tool:{name}", mapping={
            "tool": pickle.dumps(tool),
            "policy": pickle.dumps(policy),
            # ... etc
        })
    
    # Implement other ToolRegistry methods...
```

## Best Practices

1. **Use Groups for Scalability**: Instead of listing individual agents, use groups for easier management.

2. **Principle of Least Privilege**: Default to deny, explicitly allow what's needed.

3. **Policy Hierarchy**: Use tool policies for critical restrictions that should never be overridden.

4. **Audit Integration**: Combine with audit logging to track tool access:

```python
from enact import GovernanceEngine, JsonLineAuditor

auditor = JsonLineAuditor("tool_access.jsonl")
engine = GovernanceEngine(
    policy=registry.get_policy_for_tool("db", "alice"),
    auditors=[auditor]
)
```
