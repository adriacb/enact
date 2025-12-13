# Writing Custom Policies

Enact provides a flexible `Policy` interface that allows you to define complex governance logic beyond simple allow/deny lists.

## The Policy Interface

To create a custom policy, you simply implement the `Policy` protocol (a class with an `evaluate` method).

```python
from enact import Policy, GovernanceRequest, GovernanceDecision

class MyCustomPolicy(Policy):
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        # Your logic here
        return GovernanceDecision(allow=True, reason="Looks good")
```

## The Request Object

The `request` object contains:
- `agent_id`: The ID of the agent making the call.
- `tool_name`: The name of the tool (e.g., "Database", "Calculator").
- `function_name`: The method being called (e.g., "delete_table").
- `arguments`: A dictionary of arguments passed to the function.

## Examples

### 1. Time-Based Policy

Allow access only during business hours.

```python
from datetime import datetime

class BusinessHoursPolicy(Policy):
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        now = datetime.now()
        if 9 <= now.hour < 17:
            return GovernanceDecision(allow=True, reason="Business hours")
        return GovernanceDecision(allow=False, reason="After hours access denied")
```

### 2. Argument Inspection (Data Loss Prevention)

Prevent SQL injection or restricted operations based on arguments.

```python
class NoDropTablePolicy(Policy):
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        query = request.arguments.get("query", "").lower()
        if "drop table" in query:
            return GovernanceDecision(allow=False, reason="DROP TABLE is forbidden")
        return GovernanceDecision(allow=True, reason="Query allowed")
```

### 3. Stateful Policy (Rate Limiting)

Limit the number of calls an agent can make.

```python
class RateLimitPolicy(Policy):
    def __init__(self, max_calls=10):
        self.max_calls = max_calls
        self.calls = 0

    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        self.calls += 1
        if self.calls > self.max_calls:
            return GovernanceDecision(allow=False, reason="Rate limit exceeded")
        return GovernanceDecision(allow=True, reason="Under limit")
```
