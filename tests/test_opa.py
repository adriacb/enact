import pytest
from unittest.mock import patch, Mock
import requests
from enact import OPAPolicy, GovernanceRequest

def test_opa_policy_allow():
    """Test OPA policy allowing access."""
    policy = OPAPolicy("http://opa:8181", "v1/data/test/allow")
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {"result": True}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        request = GovernanceRequest("agent1", "tool", "func", {})
        decision = policy.evaluate(request)
        
        assert decision.allow is True
        assert "Allowed by OPA" in decision.reason
        
        # Verify call args
        args, kwargs = mock_post.call_args
        assert args[0] == "http://opa:8181/v1/data/test/allow"
        assert kwargs['json']['input']['agent_id'] == "agent1"

def test_opa_policy_deny_with_reason():
    """Test OPA policy denying access with reason."""
    policy = OPAPolicy("http://opa:8181", "v1/data/test/authz")
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {"result": {"allow": False, "reason": "My Custom Denial"}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        request = GovernanceRequest("agent1", "tool", "func", {})
        decision = policy.evaluate(request)
        
        assert decision.allow is False
        assert decision.reason == "My Custom Denial"

def test_opa_failure_fallback():
    """Test fallback when OPA is unreachable."""
    request = GovernanceRequest("a", "t", "f", {})

    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.RequestException("Network error")
        
        # Fail open
        policy_open = OPAPolicy("http://opa:8181", "p", default_allow=True)
        assert policy_open.evaluate(request).allow is True

        # Fail closed (default)
        policy_closed = OPAPolicy("http://opa:8181", "p", default_allow=False)
        assert policy_closed.evaluate(request).allow is False
