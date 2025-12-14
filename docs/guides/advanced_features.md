# Advanced Governance Features

This guide covers advanced governance capabilities including time-based access control, OPA integration, and correlation tracing.

## Time-Bound Access

### Tool Expiration
You can set an expiration date when registering a tool. After this date, the tool becomes inaccessible.

```python
from datetime import datetime, timedelta
from enact import InMemoryToolRegistry

registry = InMemoryToolRegistry()

# Register a temporary tool
registry.register_tool(
    name="migration_script",
    tool=my_script,
    expires_at=datetime.now() + timedelta(hours=24)
)
```

### Temporal Policy
Restrict access to specific time windows or days of the week.

```python
from datetime import time
from enact import TemporalPolicy, TimeWindow, GovernanceEngine

# Allow access only during business hours (9-5 Mon-Fri)
policy = TemporalPolicy([
    TimeWindow(
        start_time=time(9, 0),
        end_time=time(17, 0),
        days_of_week={0, 1, 2, 3, 4}  # 0=Monday
    )
])

engine = GovernanceEngine(policy=policy)
```

## OPA Integration

Delegate governance decisions to an external [Open Policy Agent](https://www.openpolicyagent.org/) server.

```python
from enact import OPAPolicy

# Delegate to local OPA instance
policy = OPAPolicy(
    url="http://localhost:8181",
    policy_path="v1/data/enact/allow",
    default_allow=False  # Fail closed if OPA is down
)
```

### OPA Request Format
Enact sends the following JSON structure to OPA:

```json
{
  "input": {
    "agent_id": "agent-1",
    "tool_name": "database",
    "function_name": "query",
    "arguments": {...},
    "context": {...},
    "correlation_id": "trace-123",
    "timestamp": "2023-10-27 10:00:00.123456"
  }
}
```

## Correlation IDs

Trace associated requests across the system using `correlation_id`. This ID is propagated to audit logs and external integrations (like OPA).

```python
from enact import GovernanceRequest

request = GovernanceRequest(
    agent_id="agent-1",
    tool_name="tool",
    function_name="func",
    arguments={},
    correlation_id="trace-550e8400-e29b-41d4-a716-446655440000"
)

# Decision and audit logs will include this ID
```
