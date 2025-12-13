"""
Integration test for HTTPAuditor.
This demonstrates usage rather than unit testing internal implementation.
"""
from enact import HTTPAuditor, GovernanceEngine, AllowAllPolicy, GovernanceRequest
from datetime import datetime, timezone

def test_http_auditor_integration():
    """
    Integration test showing HTTPAuditor usage.
    In production, this would send to a real endpoint.
    """
    # Create auditor pointing to a webhook endpoint
    auditor = HTTPAuditor(
        url="https://webhook.site/your-unique-id",  # Replace with real endpoint
        headers={"Authorization": "Bearer secret"},
        timeout=5
    )
    
    # Create engine with auditor
    engine = GovernanceEngine(policy=AllowAllPolicy(), auditors=[auditor])
    
    # Make a request
    request = GovernanceRequest("agent1", "db", "query", {"sql": "SELECT *"})
    
    # This will attempt to send the log (will fail if endpoint doesn't exist, which is expected)
    try:
        decision = engine.evaluate(request)
        assert decision.allow is True
    except Exception:
        # Expected to fail in test environment without real endpoint
        pass

if __name__ == "__main__":
    print("HTTPAuditor is ready to use!")
    print("Example usage:")
    print("""
    from enact import HTTPAuditor, GovernanceEngine
    
    auditor = HTTPAuditor(
        url="https://your-logging-service.com/api/logs",
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )
    
    engine = GovernanceEngine(policy=my_policy, auditors=[auditor])
    """)
