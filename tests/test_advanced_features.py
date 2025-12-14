import pytest
from datetime import datetime, time, timedelta
import threading
from enact import (
    ToolRegistry, InMemoryToolRegistry, 
    GovernanceEngine, GovernanceRequest,
    Auditor, AuditLog,
    TemporalPolicy, TimeWindow
)

# Temporal Policy Tests
def test_temporal_policy_window():
    """Test access control within time windows."""
    # Create window for "now"
    now = datetime.now().time()
    start = (datetime.now() - timedelta(minutes=1)).time()
    end = (datetime.now() + timedelta(minutes=1)).time()
    
    policy = TemporalPolicy([TimeWindow(start, end)])
    
    request = GovernanceRequest("agent1", "tool", "func", {})
    decision = policy.evaluate(request)
    assert decision.allow is True

def test_temporal_policy_outside_window():
    """Test blocked access outside time windows."""
    # Window in the past
    start = time(0, 0)
    end = time(0, 1)
    
    # Ensure current time is not in window
    if datetime.now().time() < end:
        start = time(23, 58)
        end = time(23, 59)
    
    policy = TemporalPolicy([TimeWindow(start, end)])
    
    request = GovernanceRequest("agent1", "tool", "func", {})
    decision = policy.evaluate(request)
    assert decision.allow is False
    assert "Outside allowed time" in decision.reason

# Tool Expiration Tests
def test_tool_registration_expiration():
    """Test tool access expiration."""
    registry = InMemoryToolRegistry()
    
    # Register tool expiring in past
    expired = datetime.now() - timedelta(seconds=1)
    registry.register_tool("legacy_tool", lambda: None, expires_at=expired)
    
    tool = registry.get_tool("legacy_tool", "agent1")
    assert tool is None

def test_tool_registration_active():
    """Test tool access before expiration."""
    registry = InMemoryToolRegistry()
    
    # Register tool expiring in future
    future = datetime.now() + timedelta(hours=1)
    registry.register_tool("active_tool", lambda: None, expires_at=future)
    
    tool = registry.get_tool("active_tool", "agent1")
    assert tool is not None

# Correlation ID Tests
class MockAuditor:
    def __init__(self):
        self.logs = []
    
    def log(self, entry: AuditLog):
        self.logs.append(entry)

def test_correlation_id_propagation():
    """Test that correlation_id is propagated to audit logs."""
    auditor = MockAuditor()
    engine = GovernanceEngine(auditors=[auditor])
    
    cid = "trace-123"
    request = GovernanceRequest(
        "agent1", "tool", "func", {},
        correlation_id=cid
    )
    
    engine.evaluate(request)
    
    assert len(auditor.logs) == 1
    assert auditor.logs[0].correlation_id == cid
