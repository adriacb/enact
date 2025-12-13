import pytest
import tempfile
import os
import json
from enact.core.interactors import GovernanceEngine
from enact.core.domain import AllowAllPolicy, GovernanceRequest
from enact.core.audit import JsonLineAuditor, AuditLog

def test_governance_engine_calls_auditor():
    """Test that GovernanceEngine invokes auditors after evaluation."""
    # Mock auditor
    class MockAuditor:
        def __init__(self):
            self.logs = []
        
        def log(self, entry: AuditLog):
            self.logs.append(entry)
    
    mock_auditor = MockAuditor()
    engine = GovernanceEngine(policy=AllowAllPolicy(), auditors=[mock_auditor])
    
    request = GovernanceRequest("agent1", "tool1", "func1", {})
    engine.evaluate(request)
    
    assert len(mock_auditor.logs) == 1
    assert mock_auditor.logs[0].agent_id == "agent1"
    assert mock_auditor.logs[0].tool == "tool1"
    assert mock_auditor.logs[0].allow is True

def test_jsonline_auditor_writes_valid_logs():
    """Test that JsonLineAuditor writes valid JSON lines."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        auditor = JsonLineAuditor(tmp_path)
        engine = GovernanceEngine(policy=AllowAllPolicy(), auditors=[auditor])
        
        # Make a request
        request = GovernanceRequest("agent1", "db", "query", {"sql": "SELECT *"})
        engine.evaluate(request)
        
        # Read the log file
        with open(tmp_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        log_entry = json.loads(lines[0])
        
        assert log_entry['agent_id'] == "agent1"
        assert log_entry['tool'] == "db"
        assert log_entry['function'] == "query"
        assert log_entry['allow'] is True
        assert 'timestamp' in log_entry
        assert 'duration_ms' in log_entry
        
    finally:
        os.remove(tmp_path)

def test_multiple_auditors():
    """Test that multiple auditors are all called."""
    class CountingAuditor:
        count = 0
        def log(self, entry):
            CountingAuditor.count += 1
    
    auditor1 = CountingAuditor()
    auditor2 = CountingAuditor()
    
    engine = GovernanceEngine(auditors=[auditor1, auditor2])
    request = GovernanceRequest("agent1", "tool", "func", {})
    engine.evaluate(request)
    
    assert CountingAuditor.count == 2
