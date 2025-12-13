import pytest
import tempfile
import os
import yaml
import json
from enact.core.policies import RuleBasedPolicy, Rule
from enact.core.domain import GovernanceRequest
from enact.config.loader import PolicyLoader

# --- RuleBasedPolicy Tests ---

def test_rule_matching_exact():
    rules = [
        Rule(tool="db", function="delete", action="deny", reason="No deletion"),
        Rule(tool="db", function="read", action="allow", reason="Reading ok")
    ]
    policy = RuleBasedPolicy(rules, default_allow=False)
    
    # Test Deny
    req_deny = GovernanceRequest("agent1", "db", "delete", {})
    decision_deny = policy.evaluate(req_deny)
    assert decision_deny.allow is False
    assert "No deletion" in decision_deny.reason
    
    # Test Allow
    req_allow = GovernanceRequest("agent1", "db", "read", {})
    decision_allow = policy.evaluate(req_allow)
    assert decision_allow.allow is True

def test_rule_wildcard_translation():
    # User might input "*" for wildcard
    # The current implementation in policies.py translates "*" -> ".*"
    # Testing that logic
    rules = [
        Rule(tool="*", function="safe_.*", action="allow", reason="All safe functions ok")
    ]
    policy = RuleBasedPolicy(rules)
    
    req = GovernanceRequest("agent1", "SystemTool", "safe_execute", {})
    decision = policy.evaluate(req)
    assert decision.allow is True

def test_default_fallback():
    policy = RuleBasedPolicy(rules=[], default_allow=False)
    req = GovernanceRequest("agent1", "unknown", "func", {})
    assert policy.evaluate(req).allow is False

# --- PolicyLoader Tests ---

def test_load_yaml_config():
    config_data = {
        "default_allow": False,
        "rules": [
            {"tool": "db", "function": "drop", "action": "deny", "reason": "No drop"},
            {"tool": "db", "function": "*", "action": "allow"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        yaml.dump(config_data, tmp)
        tmp_path = tmp.name
        
    try:
        policy = PolicyLoader.load(tmp_path)
        assert isinstance(policy, RuleBasedPolicy)
        assert len(policy.rules) == 2
        assert policy.rules[0].reason == "No drop"
        
        # Verify it works
        req = GovernanceRequest("a", "db", "drop", {})
        assert policy.evaluate(req).allow is False
        
        req2 = GovernanceRequest("a", "db", "select", {})
        assert policy.evaluate(req2).allow is True
        
    finally:
        os.remove(tmp_path)

def test_load_json_config():
    config_data = {
        "default_allow": True,
        "rules": []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
        json.dump(config_data, tmp)
        tmp_path = tmp.name
        
    try:
        policy = PolicyLoader.load(tmp_path)
        assert policy.default_allow is True
        
    finally:
        os.remove(tmp_path)
