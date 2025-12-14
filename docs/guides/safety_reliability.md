# Safety & Reliability Guide

This guide covers the production-grade safety features in Enact that protect against failures, cascading errors, and resource exhaustion.

## Overview

Enact provides five key safety mechanisms:

1. **Rate Limiting** - Control request frequency
2. **Action Quotas** - Limit total actions over time
3. **Circuit Breakers** - Prevent cascading failures
4. **Timeouts & Retries** - Handle transient failures
5. **Dry-Run Mode** - Simulate without executing

## Rate Limiting

Prevents agents from overwhelming tools with too many requests.

### Basic Usage

```python
from enact import RateLimiter

# Allow 60 calls per minute with burst of 10
limiter = RateLimiter(max_calls_per_minute=60, burst_size=10)

# Check before executing
if limiter.check_limit("agent1", "database"):
    result = database.query("SELECT *")
else:
    print("Rate limit exceeded")
```

### How It Works

Uses the **token bucket algorithm**:
- Tokens refill at a steady rate (e.g., 1 per second for 60/min)
- Burst size allows temporary spikes
- Each request consumes one token

### Advanced Usage

```python
# Check remaining tokens
remaining = limiter.get_remaining("agent1", "database")
print(f"Remaining calls: {remaining}")

# Reset limit for agent-tool
limiter.reset("agent1", "database")
```

### Best Practices

- Set `max_calls_per_minute` based on tool capacity
- Use `burst_size` to allow short spikes
- Different limits for different tools (read vs. write)

---

## Action Quotas

Limits total actions within a rolling time window.

### Basic Usage

```python
from enact import QuotaManager, QuotaConfig

# 1000 actions per 24 hours
manager = QuotaManager(QuotaConfig(max_actions=1000, window_hours=24))

# Consume quota
if manager.consume("agent1", "api_call"):
    result = api.call()
else:
    print("Quota exceeded")
```

### Per-Agent Quotas

```python
# Custom quota for specific agent
manager.set_quota("premium_agent", QuotaConfig(max_actions=10000, window_hours=24))
manager.set_quota("free_agent", QuotaConfig(max_actions=100, window_hours=24))
```

### Monitoring

```python
# Check remaining quota
remaining = manager.get_remaining("agent1")
print(f"Remaining actions: {remaining}")

# Reset quota
manager.reset("agent1")
```

### Use Cases

- **Cost Control**: Limit expensive API calls
- **Fair Usage**: Prevent single agent from monopolizing resources
- **Compliance**: Enforce usage limits per SLA

---

## Circuit Breakers

Prevents cascading failures by stopping requests to failing tools.

### Basic Usage

```python
from enact import CircuitBreaker, CircuitBreakerOpen

breaker = CircuitBreaker()

# Check before calling
if breaker.is_open("external_api"):
    print("Circuit open - service unavailable")
else:
    try:
        result = external_api.call()
        breaker.record_success("external_api")
    except Exception as e:
        breaker.record_failure("external_api")
        raise
```

### States

1. **CLOSED** (Normal)
   - Requests pass through
   - Failures are counted

2. **OPEN** (Blocking)
   - All requests blocked
   - Entered after threshold failures
   - Waits for timeout before trying again

3. **HALF_OPEN** (Testing)
   - Limited requests allowed
   - Testing if service recovered
   - Success → CLOSED, Failure → OPEN

### Configuration

```python
from enact import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,      # Open after 5 failures
    success_threshold=2,      # Close after 2 successes in half-open
    timeout_seconds=60        # Wait 60s before trying half-open
)

breaker = CircuitBreaker(config)
```

### Monitoring

```python
from enact import CircuitState

state = breaker.get_state("api")
if state == CircuitState.OPEN:
    print("Service is down")
elif state == CircuitState.HALF_OPEN:
    print("Testing recovery")
```

---

## Timeouts & Retries

Handle transient failures with automatic retries and timeouts.

### ReliableToolProxy

Wraps tools with both timeout and retry logic:

```python
from enact import ReliableToolProxy, RetryConfig

reliable_api = ReliableToolProxy(
    api_tool,
    timeout_seconds=30,
    retry_config=RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        exponential_base=2.0,
        jitter=True
    )
)

# Automatic retries with exponential backoff
result = reliable_api.call()
```

### Decorators

For more control, use decorators directly:

```python
from enact.reliability import with_timeout, with_retry, RetryConfig

@with_timeout(30)
@with_retry(RetryConfig(max_attempts=3))
def call_api():
    return api.request()
```

### Retry Configuration

```python
RetryConfig(
    max_attempts=3,        # Try up to 3 times
    initial_delay=1.0,     # Start with 1s delay
    max_delay=60.0,        # Cap at 60s
    exponential_base=2.0,  # Double delay each retry (1s, 2s, 4s...)
    jitter=True            # Add randomness to prevent thundering herd
)
```

### Error Handling

```python
from enact.reliability import MaxRetriesExceeded, TimeoutError

try:
    result = reliable_api.call()
except TimeoutError:
    print("Operation timed out")
except MaxRetriesExceeded as e:
    print(f"Failed after retries: {e}")
```

---

## Dry-Run Mode

Simulate tool execution without actually running it.

### Basic Usage

```python
from enact import DryRunProxy

# Wrap tool in dry-run mode
dry_run = DryRunProxy(database_tool, "database")

# Simulates without executing
result = dry_run.delete_all_records()

print(result.would_execute)  # "database.delete_all_records()"
print(result.estimated_impact)  # "HIGH - Destructive operation"
```

### Impact Estimation

Automatically estimates operation impact:

- **HIGH**: `delete`, `remove`, `drop`
- **MEDIUM**: `create`, `insert`, `update`
- **LOW**: `read`, `get`, `query`, `select`

### Tracking Executions

```python
# Execute multiple operations
dry_run.create_user("alice")
dry_run.delete_user("bob")
dry_run.query_users()

# Review what would have happened
for execution in dry_run.get_executions():
    print(f"{execution.function_name}: {execution.estimated_impact}")

# Clear history
dry_run.clear_executions()
```

### Use Cases

- **Testing Policies**: Verify governance without side effects
- **Agent Development**: Understand agent behavior
- **Debugging**: Trace what an agent would do
- **Demos**: Show capabilities safely

---

## Combining Safety Features

Use multiple features together for comprehensive protection:

```python
from enact import (
    RateLimiter, CircuitBreaker, ReliableToolProxy,
    RetryConfig, DryRunProxy
)

# Setup safety layers
rate_limiter = RateLimiter(max_calls_per_minute=60)
circuit_breaker = CircuitBreaker()

# Wrap tool with resilience
reliable_tool = ReliableToolProxy(
    my_tool,
    timeout_seconds=30,
    retry_config=RetryConfig(max_attempts=3)
)

# Check safety before execution
def safe_execute(agent_id, tool_name, operation):
    # Check rate limit
    if not rate_limiter.check_limit(agent_id, tool_name):
        return {"error": "Rate limit exceeded"}
    
    # Check circuit breaker
    if circuit_breaker.is_open(tool_name):
        return {"error": "Service unavailable"}
    
    # Execute with resilience
    try:
        result = operation()
        circuit_breaker.record_success(tool_name)
        return {"result": result}
    except Exception as e:
        circuit_breaker.record_failure(tool_name)
        return {"error": str(e)}
```

---

## Best Practices

### 1. Layer Safety Features

```python
# Rate limit → Circuit breaker → Retry → Execute
if rate_limiter.check_limit(agent, tool):
    if not circuit_breaker.is_open(tool):
        reliable_tool.execute()
```

### 2. Configure Based on Tool Characteristics

```python
# Fast, reliable tools
fast_config = RetryConfig(max_attempts=2, initial_delay=0.5)

# Slow, flaky tools
slow_config = RetryConfig(max_attempts=5, initial_delay=2.0, max_delay=30.0)
```

### 3. Monitor and Alert

```python
# Alert when circuit opens
if breaker.get_state("critical_api") == CircuitState.OPEN:
    send_alert("Critical API is down!")

# Alert on quota exhaustion
if quota_manager.get_remaining("agent") < 10:
    send_warning("Agent quota running low")
```

### 4. Use Dry-Run for Testing

```python
# Test new policies safely
dry_run = DryRunProxy(tool, "tool")
for i in range(100):
    dry_run.operation()

# Analyze impact
high_impact = [e for e in dry_run.get_executions() if "HIGH" in e.estimated_impact]
print(f"High-impact operations: {len(high_impact)}")
```

---

## Performance Considerations

### Rate Limiter
- **Memory**: O(number of agent-tool combinations)
- **CPU**: O(1) per check
- **Cleanup**: Tokens refill automatically

### Quota Manager
- **Memory**: O(number of agents × window size)
- **CPU**: O(window size) per check
- **Cleanup**: Old entries cleaned automatically

### Circuit Breaker
- **Memory**: O(number of tools)
- **CPU**: O(1) per check
- **State**: Persists until manually reset

### Retries
- **Latency**: Adds delay on failures (exponential backoff)
- **CPU**: Minimal overhead
- **Network**: Multiple attempts on failure
