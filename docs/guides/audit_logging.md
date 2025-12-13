# Audit Logging Guide

Enact provides comprehensive audit logging to track all governance decisions for compliance, monitoring, and debugging.

## Overview

Audit logging captures:
- Timestamp of the decision
- Agent ID making the request
- Tool and function being accessed
- Arguments passed
- Allow/Deny decision
- Reason for the decision
- Execution duration

## Available Auditors

### 1. JsonLineAuditor (Local Files)

Writes audit logs to a local file in JSON Lines format.

```python
from enact import JsonLineAuditor, GovernanceEngine

auditor = JsonLineAuditor("audit.jsonl")
engine = GovernanceEngine(policy=my_policy, auditors=[auditor])
```

**Log Format:**
```json
{"timestamp": "2025-12-13T23:00:00+00:00", "agent_id": "agent1", "tool": "database", "function": "query", "arguments": {"sql": "SELECT *"}, "allow": true, "reason": "Allowed", "duration_ms": 1.2}
```

### 2. HTTPAuditor (Remote Endpoints)

Sends audit logs to an HTTP endpoint (webhooks, logging services, etc.).

```python
from enact import HTTPAuditor

auditor = HTTPAuditor(
    url="https://logs.example.com/api/audit",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    timeout=5
)

engine = GovernanceEngine(policy=my_policy, auditors=[auditor])
```

**Use Cases:**
- Send to Datadog, Splunk, or other logging platforms
- Trigger webhooks on policy violations
- Real-time monitoring dashboards

### 3. SyslogAuditor (Syslog Integration)

Sends logs to a syslog server for centralized logging.

```python
from enact import SyslogAuditor

auditor = SyslogAuditor(
    host="syslog.example.com",
    port=514,
    facility=16  # local0
)

engine = GovernanceEngine(policy=my_policy, auditors=[auditor])
```

**Compatible with:**
- rsyslog
- syslog-ng
- Any RFC 5424 compliant syslog daemon

### 4. CloudWatchAuditor (AWS CloudWatch Logs)

Sends logs to AWS CloudWatch for cloud-native monitoring.

```python
from enact import CloudWatchAuditor

# Requires: pip install enact[cloud]
auditor = CloudWatchAuditor(
    log_group="/enact/governance",
    log_stream="production",
    region="us-east-1"
)

engine = GovernanceEngine(policy=my_policy, auditors=[auditor])
```

**Features:**
- Auto-creates log groups and streams
- Handles sequence tokens automatically
- Integrates with CloudWatch Insights for querying

## Multiple Auditors

You can use multiple auditors simultaneously:

```python
from enact import JsonLineAuditor, HTTPAuditor, GovernanceEngine

# Local backup
local_auditor = JsonLineAuditor("local_audit.jsonl")

# Remote monitoring
remote_auditor = HTTPAuditor(
    url="https://monitoring.example.com/audit",
    headers={"X-API-Key": "secret"}
)

# Both will receive logs
engine = GovernanceEngine(
    policy=my_policy,
    auditors=[local_auditor, remote_auditor]
)
```

## Custom Auditors

Implement the `Auditor` protocol to create custom auditors:

```python
from enact.core.audit import Auditor, AuditLog
import psycopg2

class PostgresAuditor:
    """Store audit logs in PostgreSQL."""
    
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
    
    def log(self, entry: AuditLog) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs 
            (timestamp, agent_id, tool, function, allow, reason, duration_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            entry.timestamp,
            entry.agent_id,
            entry.tool,
            entry.function,
            entry.allow,
            entry.reason,
            entry.duration_ms
        ))
        self.conn.commit()
```

## Analyzing Audit Logs

### JSON Lines (Local Files)

```python
import json

# Read and analyze logs
with open("audit.jsonl", "r") as f:
    for line in f:
        log = json.loads(line)
        if not log["allow"]:
            print(f"Denied: {log['agent_id']} tried to access {log['tool']}.{log['function']}")
```

### CloudWatch Insights Queries

```sql
-- Find all denied requests
fields @timestamp, agent_id, tool, function, reason
| filter allow = false
| sort @timestamp desc

-- Count requests by agent
stats count() by agent_id
| sort count desc

-- Average execution time by tool
stats avg(duration_ms) by tool
```

## Best Practices

### 1. Error Handling

All auditors handle errors gracefully and won't crash your governance flow:

```python
# Even if the HTTP endpoint is down, governance continues
auditor = HTTPAuditor(url="https://unreachable.com/logs")
engine = GovernanceEngine(policy=policy, auditors=[auditor])

# This will still work, auditor errors are logged but not raised
decision = engine.evaluate(request)
```

### 2. Performance Considerations

Auditors are called synchronously. For high-throughput systems:

```python
# Use async auditors or queue-based solutions
class AsyncHTTPAuditor:
    def __init__(self, url):
        self.url = url
        self.queue = Queue()
        self.worker = Thread(target=self._process_queue)
        self.worker.start()
    
    def log(self, entry):
        self.queue.put(entry)  # Non-blocking
    
    def _process_queue(self):
        while True:
            entry = self.queue.get()
            # Send to HTTP endpoint
```

### 3. Sensitive Data

Avoid logging sensitive arguments:

```python
from enact.core.audit import AuditLog
from dataclasses import replace

class RedactedAuditor:
    def __init__(self, base_auditor):
        self.base = base_auditor
    
    def log(self, entry: AuditLog):
        # Redact sensitive fields
        safe_args = {
            k: "***REDACTED***" if k in ["password", "token", "secret"] else v
            for k, v in entry.arguments.items()
        }
        
        redacted_entry = replace(entry, arguments=safe_args)
        self.base.log(redacted_entry)
```

### 4. Retention Policies

For `JsonLineAuditor`, implement log rotation:

```python
from logging.handlers import RotatingFileHandler
import logging

# Use Python's logging with rotation
logger = logging.getLogger("enact.audit")
handler = RotatingFileHandler(
    "audit.jsonl",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
logger.addHandler(handler)
```

## Compliance Use Cases

### SOC 2 Compliance

```python
# Track all access to sensitive data
sensitive_auditor = JsonLineAuditor("compliance/soc2_audit.jsonl")

engine = GovernanceEngine(
    policy=strict_policy,
    auditors=[sensitive_auditor]
)
```

### GDPR Data Access Logs

```python
# Log all personal data access
gdpr_auditor = HTTPAuditor(
    url="https://compliance.example.com/gdpr/audit",
    headers={"X-Compliance": "GDPR"}
)
```

### Real-time Alerting

```python
class AlertAuditor:
    """Send alerts on policy violations."""
    
    def log(self, entry: AuditLog):
        if not entry.allow:
            # Send alert
            send_slack_alert(
                f"⚠️ Policy violation: {entry.agent_id} tried to access "
                f"{entry.tool}.{entry.function} - {entry.reason}"
            )
```
