# Human Oversight Guide

This guide covers the human oversight features that ensure critical agent actions require human approval and provide emergency controls.

## Overview

Enact provides three key oversight mechanisms:

1. **Approval Workflows** - Require human approval for high-risk operations
2. **Kill Switch** - Emergency stop for all agent operations
3. **Confidence-Based Escalation** - Automatic escalation when agent confidence is low

## Approval Workflows

Require human approval before executing high-risk operations.

### Basic Usage

```python
from enact import ApprovalWorkflow

# Define high-risk tools
workflow = ApprovalWorkflow(
    high_risk_tools={"database", "payment_api"},
    high_risk_functions={"delete.*", ".*_all"}  # Regex patterns
)

# Check if approval needed
if workflow.requires_approval("agent1", "database", "delete_all", {}):
    # Request approval
    request = workflow.request_approval(
        agent_id="agent1",
        tool_name="database",
        function_name="delete_all",
        arguments={"table": "users"},
        justification="Cleanup old test data",
        risk_level="HIGH"
    )
    
    print(f"Approval request ID: {request.id}")
    print(f"Status: {request.status}")  # PENDING
    
    # Wait for human approval...
```

### Approving/Rejecting Requests

```python
# Get pending requests
pending = workflow.get_pending_requests()
for request in pending:
    print(f"Agent {request.agent_id} wants to {request.function_name}")
    print(f"Risk: {request.risk_level}")
    print(f"Justification: {request.justification}")

# Approve a request
workflow.approve(request.id, approver="admin")

# Or reject it
workflow.reject(
    request.id,
    approver="admin",
    reason="Too risky without backup"
)

# Check status
from enact.oversight import ApprovalStatus
status = workflow.get_status(request.id)
if status == ApprovalStatus.APPROVED:
    # Proceed with operation
    pass
```

### Approval Callbacks

Get notified when approval is requested:

```python
def send_notification(request):
    """Send email/Slack notification to approvers."""
    print(f"⚠️ Approval needed: {request.tool_name}.{request.function_name}")
    print(f"Risk: {request.risk_level}")
    # Send email, Slack message, etc.

workflow = ApprovalWorkflow(approval_callback=send_notification)
```

### Integration Example

```python
from enact import ApprovalWorkflow, GovernanceEngine

workflow = ApprovalWorkflow(high_risk_tools={"database"})
engine = GovernanceEngine(policy=my_policy)

def safe_execute(agent_id, tool, function, args):
    # Check if approval needed
    if workflow.requires_approval(agent_id, tool.__class__.__name__, function, args):
        request = workflow.request_approval(
            agent_id, tool.__class__.__name__, function, args
        )
        
        # Wait for approval (in production, this would be async)
        while workflow.get_status(request.id) == ApprovalStatus.PENDING:
            time.sleep(1)
        
        if workflow.get_status(request.id) != ApprovalStatus.APPROVED:
            raise PermissionError("Operation not approved")
    
    # Execute with governance
    return getattr(tool, function)(**args)
```

---

## Kill Switch

Emergency stop mechanism to immediately halt all agent operations.

### Basic Usage

```python
from enact import KillSwitch

# Get the kill-switch (singleton)
switch = KillSwitch()

# Check before operations
if not switch.check():
    raise Exception("Operations halted by kill-switch")

# Activate in emergency
switch.activate(
    activated_by="admin",
    reason="Security incident detected"
)

# All operations will now be blocked
assert switch.is_active() is True
assert switch.check() is False
```

### With Callback

```python
def emergency_alert(switch):
    """Alert all systems when kill-switch activated."""
    status = switch.get_status()
    print(f"🚨 KILL-SWITCH ACTIVATED")
    print(f"By: {status['activated_by']}")
    print(f"Reason: {status['reason']}")
    # Send alerts, log to security system, etc.

switch.activate("admin", "Suspicious activity", callback=emergency_alert)
```

### Integration with Governance

```python
from enact import KillSwitch, GovernanceEngine
from enact.oversight import KillSwitchActive

switch = KillSwitch()
engine = GovernanceEngine(policy=my_policy)

def execute_with_killswitch(request):
    # Check kill-switch first
    if not switch.check():
        status = switch.get_status()
        raise KillSwitchActive(status['reason'])
    
    # Proceed with governance
    decision = engine.evaluate(request)
    if decision.allow:
        # Execute...
        pass
```

### Monitoring

```python
# Get detailed status
status = switch.get_status()
print(f"Active: {status['active']}")
print(f"Activated at: {status['activated_at']}")
print(f"Activated by: {status['activated_by']}")
print(f"Reason: {status['reason']}")

# Deactivate when safe
switch.deactivate("admin")
```

### Best Practices

1. **Monitor Activation**: Log all kill-switch activations
2. **Clear Communication**: Always provide clear reason
3. **Controlled Deactivation**: Require authorization to deactivate
4. **Test Regularly**: Include in disaster recovery drills

---

## Confidence-Based Escalation

Automatically escalate to human oversight when agent confidence is low.

### Basic Usage

```python
from enact import ConfidenceEscalation, EscalationLevel

escalation = ConfidenceEscalation()

# Agent reports confidence with request
confidence = 0.4  # Low confidence

decision = escalation.evaluate(
    confidence=confidence,
    agent_id="agent1",
    tool_name="database",
    function_name="complex_query",
    context={"query_complexity": "high"}
)

print(f"Escalation level: {decision.level}")
print(f"Requires human: {decision.requires_human}")
print(f"Message: {decision.message}")

if decision.requires_human:
    # Escalate to human review/approval
    pass
```

### Escalation Levels

Based on confidence score:

| Confidence | Level | Action | Requires Human |
|-----------|-------|--------|----------------|
| ≥ 0.9 | NONE | Proceed | No |
| ≥ 0.7 | NOTIFY | Notify human | No |
| ≥ 0.5 | REVIEW | Require review | Yes |
| < 0.5 | APPROVAL | Require approval | Yes |

### Custom Thresholds

```python
from enact.oversight import ConfidenceThresholds

# More conservative thresholds
thresholds = ConfidenceThresholds(
    high=0.95,    # Very high confidence required
    medium=0.80,
    low=0.60
)

escalation = ConfidenceEscalation(thresholds=thresholds)
```

### Callbacks for Each Level

```python
def notify_human(agent_id, tool, func, confidence, context):
    print(f"ℹ️ Agent {agent_id} has medium confidence ({confidence})")

def request_review(agent_id, tool, func, confidence, context):
    print(f"⚠️ Agent {agent_id} needs review ({confidence})")
    # Create review ticket

def request_approval(agent_id, tool, func, confidence, context):
    print(f"🚨 Agent {agent_id} needs approval ({confidence})")
    # Block and request approval

escalation = ConfidenceEscalation(
    notify_callback=notify_human,
    review_callback=request_review,
    approval_callback=request_approval
)
```

### Integration Example

```python
from enact import ConfidenceEscalation, ApprovalWorkflow

escalation = ConfidenceEscalation()
approval_workflow = ApprovalWorkflow()

def execute_with_confidence(agent_id, tool, func, args, confidence):
    # Evaluate confidence
    decision = escalation.evaluate(confidence, agent_id, tool, func)
    
    if decision.level == EscalationLevel.APPROVAL:
        # Require approval
        request = approval_workflow.request_approval(
            agent_id, tool, func, args,
            justification=f"Low confidence: {confidence}"
        )
        # Wait for approval...
    
    elif decision.level == EscalationLevel.REVIEW:
        # Log for human review
        log_for_review(agent_id, tool, func, confidence)
    
    # Execute if allowed
    if not decision.requires_human or is_approved(request):
        return execute_tool(tool, func, args)
```

---

## Combining Oversight Features

Use all three mechanisms together for comprehensive human oversight:

```python
from enact import ApprovalWorkflow, KillSwitch, ConfidenceEscalation

# Setup
workflow = ApprovalWorkflow(high_risk_tools={"payment"})
switch = KillSwitch()
escalation = ConfidenceEscalation()

def execute_with_oversight(agent_id, tool_name, func, args, confidence=1.0):
    # 1. Check kill-switch first
    if not switch.check():
        raise KillSwitchActive("System halted")
    
    # 2. Check confidence-based escalation
    esc_decision = escalation.evaluate(confidence, agent_id, tool_name, func)
    
    # 3. Check if approval needed (high-risk or low confidence)
    needs_approval = (
        workflow.requires_approval(agent_id, tool_name, func, args) or
        esc_decision.level == EscalationLevel.APPROVAL
    )
    
    if needs_approval:
        request = workflow.request_approval(
            agent_id, tool_name, func, args,
            justification=f"Confidence: {confidence}",
            risk_level="HIGH" if confidence < 0.5 else "MEDIUM"
        )
        
        # Wait for approval
        if not wait_for_approval(request.id):
            raise PermissionError("Operation not approved")
    
    # 4. Execute with governance
    return execute_tool(tool_name, func, args)
```

---

## Best Practices

### 1. Layer Oversight Controls

```python
# Kill-switch → Confidence → Approval → Governance → Execute
if switch.check():
    if confidence > 0.5 or is_approved():
        if policy.allows():
            execute()
```

### 2. Clear Justifications

```python
# Always provide context
request = workflow.request_approval(
    agent_id, tool, func, args,
    justification="Deleting 1000 old records to free space. Backup completed.",
    risk_level="MEDIUM"
)
```

### 3. Audit All Decisions

```python
# Log all approval decisions
def log_approval(request, decision):
    audit_log.write({
        "type": "approval",
        "request_id": request.id,
        "decision": decision,
        "approver": approver,
        "timestamp": datetime.now()
    })
```

### 4. Test Emergency Procedures

```python
# Regular kill-switch drills
def test_kill_switch():
    switch.activate("test", "Drill")
    assert all_operations_blocked()
    switch.deactivate("test")
```

---

## Use Cases

### Financial Transactions

```python
workflow = ApprovalWorkflow(high_risk_tools={"payment_api"})
escalation = ConfidenceEscalation(
    thresholds=ConfidenceThresholds(high=0.95, medium=0.85, low=0.70)
)

# High confidence required for payments
```

### Data Deletion

```python
workflow = ApprovalWorkflow(
    high_risk_functions={"delete.*", "drop.*", "truncate.*"}
)

# All delete operations require approval
```

### Security Incidents

```python
switch = KillSwitch()

def on_security_alert(alert):
    if alert.severity == "CRITICAL":
        switch.activate("security_system", f"Alert: {alert.message}")
```

### Low-Confidence Operations

```python
escalation = ConfidenceEscalation()

# Agent unsure about complex decision
if agent_confidence < 0.6:
    decision = escalation.evaluate(agent_confidence, ...)
    if decision.requires_human:
        # Escalate to human expert
```
