import pytest
from enact.oversight import (
    ApprovalWorkflow, ApprovalStatus,
    KillSwitch, KillSwitchActive,
    ConfidenceEscalation, EscalationLevel, ConfidenceThresholds
)

# Approval Workflow Tests
def test_approval_workflow_requires_approval():
    """Test that high-risk tools require approval."""
    workflow = ApprovalWorkflow(high_risk_tools={"database", "payment"})
    
    assert workflow.requires_approval("agent1", "database", "delete", {}) is True
    assert workflow.requires_approval("agent1", "calculator", "add", {}) is False

def test_approval_workflow_request():
    """Test creating an approval request."""
    workflow = ApprovalWorkflow()
    
    request = workflow.request_approval(
        "agent1", "database", "delete_all", {},
        justification="Cleanup old data",
        risk_level="HIGH"
    )
    
    assert request.status == ApprovalStatus.PENDING
    assert request.agent_id == "agent1"
    assert request.risk_level == "HIGH"
    assert len(workflow.get_pending_requests()) == 1

def test_approval_workflow_approve():
    """Test approving a request."""
    workflow = ApprovalWorkflow()
    
    request = workflow.request_approval("agent1", "tool", "func", {})
    assert workflow.approve(request.id, "admin") is True
    
    assert workflow.get_status(request.id) == ApprovalStatus.APPROVED
    assert len(workflow.get_pending_requests()) == 0

def test_approval_workflow_reject():
    """Test rejecting a request."""
    workflow = ApprovalWorkflow()
    
    request = workflow.request_approval("agent1", "tool", "func", {})
    assert workflow.reject(request.id, "admin", "Too risky") is True
    
    assert workflow.get_status(request.id) == ApprovalStatus.REJECTED

def test_approval_workflow_callback():
    """Test that callback is triggered on request."""
    called = []
    
    def callback(request):
        called.append(request)
    
    workflow = ApprovalWorkflow(approval_callback=callback)
    request = workflow.request_approval("agent1", "tool", "func", {})
    
    assert len(called) == 1
    assert called[0].id == request.id

# Kill Switch Tests
def test_kill_switch_singleton():
    """Test that KillSwitch is a singleton."""
    switch1 = KillSwitch()
    switch2 = KillSwitch()
    
    assert switch1 is switch2

def test_kill_switch_activate():
    """Test activating the kill-switch."""
    switch = KillSwitch()
    switch.reset()  # Ensure clean state
    
    assert switch.is_active() is False
    assert switch.check() is True
    
    switch.activate("admin", "Emergency stop")
    
    assert switch.is_active() is True
    assert switch.check() is False

def test_kill_switch_deactivate():
    """Test deactivating the kill-switch."""
    switch = KillSwitch()
    switch.reset()
    
    switch.activate("admin", "Test")
    assert switch.is_active() is True
    
    switch.deactivate("admin")
    assert switch.is_active() is False

def test_kill_switch_status():
    """Test getting kill-switch status."""
    switch = KillSwitch()
    switch.reset()
    
    switch.activate("admin", "Emergency")
    status = switch.get_status()
    
    assert status["active"] is True
    assert status["activated_by"] == "admin"
    assert status["reason"] == "Emergency"

# Confidence Escalation Tests
def test_confidence_escalation_high():
    """Test that high confidence doesn't escalate."""
    escalation = ConfidenceEscalation()
    
    decision = escalation.evaluate(0.95, "agent1", "tool", "func")
    
    assert decision.level == EscalationLevel.NONE
    assert decision.requires_human is False

def test_confidence_escalation_medium():
    """Test that medium confidence triggers notification."""
    escalation = ConfidenceEscalation()
    
    decision = escalation.evaluate(0.75, "agent1", "tool", "func")
    
    assert decision.level == EscalationLevel.NOTIFY
    assert decision.requires_human is False

def test_confidence_escalation_low():
    """Test that low confidence requires review."""
    escalation = ConfidenceEscalation()
    
    decision = escalation.evaluate(0.55, "agent1", "tool", "func")
    
    assert decision.level == EscalationLevel.REVIEW
    assert decision.requires_human is True

def test_confidence_escalation_very_low():
    """Test that very low confidence requires approval."""
    escalation = ConfidenceEscalation()
    
    decision = escalation.evaluate(0.3, "agent1", "tool", "func")
    
    assert decision.level == EscalationLevel.APPROVAL
    assert decision.requires_human is True

def test_confidence_escalation_callbacks():
    """Test that callbacks are triggered at appropriate levels."""
    notifications = []
    reviews = []
    approvals = []
    
    escalation = ConfidenceEscalation(
        notify_callback=lambda *args: notifications.append(args),
        review_callback=lambda *args: reviews.append(args),
        approval_callback=lambda *args: approvals.append(args)
    )
    
    # High confidence - no callbacks
    escalation.evaluate(0.95, "agent1", "tool", "func")
    assert len(notifications) == 0
    
    # Medium - notify
    escalation.evaluate(0.75, "agent1", "tool", "func")
    assert len(notifications) == 1
    
    # Low - review
    escalation.evaluate(0.55, "agent1", "tool", "func")
    assert len(reviews) == 1
    
    # Very low - approval
    escalation.evaluate(0.3, "agent1", "tool", "func")
    assert len(approvals) == 1

def test_confidence_escalation_custom_thresholds():
    """Test custom confidence thresholds."""
    thresholds = ConfidenceThresholds(high=0.8, medium=0.6, low=0.4)
    escalation = ConfidenceEscalation(thresholds=thresholds)
    
    # 0.75 should be NOTIFY with custom thresholds
    decision = escalation.evaluate(0.75, "agent1", "tool", "func")
    assert decision.level == EscalationLevel.NOTIFY
