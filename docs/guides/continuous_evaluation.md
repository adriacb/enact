# Continuous Evaluation

Enact provides tools to monitor, evaluate, and stress-test your AI agent governance.

## Usage Metrics

Track tool usage, error rates, and policy denials.

```python
from enact import UsageTracker

tracker = UsageTracker()

# In your tool execution loop:
tracker.record_usage(
    agent_id="agent-1",
    tool_name="database",
    success=True,
    duration_ms=120,
    allowed=True
)

# Get insights
print(tracker.get_tool_metrics("database"))
# {'call_count': 1, 'error_rate': 0.0, 'avg_duration_ms': 120.0, ...}
```

## Anomaly Detection

Detect suspicious behavior patterns like high error rates or frequent denials.

```python
from enact import AnomalyDetector

detector = AnomalyDetector(tracker)
anomalies = detector.detect_anomalies()

for anomaly in anomalies:
    print(f"[{anomaly.severity}] {anomaly.description} ({anomaly.metric}={anomaly.value})")
```

## Red-Teaming Framework

Simulate attacks to verify your governance coverage.

```python
from enact import RedTeamSimulator, RedTeamScenario, GovernanceEngine

# 1. Setup Engine
engine = GovernanceEngine(...)
simulator = RedTeamSimulator(engine)

# 2. Define Scenarios
scenarios = [
    RedTeamScenario(
        name="SQL Injection Attempt",
        description="Attempt to inject malicious SQL",
        tool_name="db",
        function_name="query",
        arguments={"sql": "DROP TABLE users;"},
        should_be_blocked=True
    ),
    RedTeamScenario(
        name="Valid Access",
        tool_name="db",
        function_name="select",
        arguments={"id": 1},
        should_be_blocked=False
    )
]

# 3. Run Simulation
results = simulator.run_suite(scenarios)

# 4. Analyze Results
summary = simulator.get_summary()
print(f"Vulnerabilities Found: {summary['vulnerabilities_found']}")
```
