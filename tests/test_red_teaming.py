import pytest
from enact import (
    RedTeamSimulator, RedTeamScenario, 
    GovernanceEngine, AllowAllPolicy, RuleBasedPolicy, Rule
)

class DenyAllPolicy:
    def evaluate(self, request):
        from enact import GovernanceDecision
        return GovernanceDecision(False, "Denied")

def test_red_team_attack_succeeds_():
    """
    Test case where the governance fails to block a malicious request.
    This means the attack SUCCEEDS (bad for us).
    """
    # System allows everything (Vulnerable)
    engine = GovernanceEngine(policy=AllowAllPolicy())
    simulator = RedTeamSimulator(engine)
    
    scenario = RedTeamScenario(
        name="SQL Injection",
        description="Try to drop tables",
        tool_name="database",
        function_name="query",
        arguments={"sql": "DROP TABLE users"},
        should_be_blocked=True
    )
    
    result = simulator.run_scenario(scenario)
    
    # Attack should SUCCEED because policy allowed it
    assert result.success is True 
    assert result.blocked is False
    assert "Attack succeeded" in result.details

def test_red_team_attack_blocked():
    """
    Test case where governance correctly blocks a request.
    This means attack FAILS (good for us).
    """
    # System blocks everything (Safe)
    engine = GovernanceEngine(policy=DenyAllPolicy())
    simulator = RedTeamSimulator(engine)
    
    scenario = RedTeamScenario(
        name="Unauthorized Access",
        description="Try to access admin tool",
        tool_name="admin",
        function_name="delete",
        arguments={},
        should_be_blocked=True
    )
    
    result = simulator.run_scenario(scenario)
    
    # Attack should FAIL because it was blocked
    assert result.success is False
    assert result.blocked is True
    assert "Attack failed" in result.details

def test_red_team_summary():
    """Test results summary."""
    engine = GovernanceEngine(policy=AllowAllPolicy())
    simulator = RedTeamSimulator(engine)
        
    scenarios = [
        RedTeamScenario("A1", "", "t", "f", {}, should_be_blocked=True), # Will succeed (vuln)
        RedTeamScenario("A2", "", "t", "f", {}, should_be_blocked=False) # Will fail (safe)
    ]
    
    simulator.run_suite(scenarios)
    summary = simulator.get_summary()
    
    # A1: Expected block, got allow -> Attack Success -> Vuln
    # A2: Expected allow, got allow -> blocked=False != True -> Success=False -> Safe
    
    # Wait, if should_be_blocked=False (we expect Allow), and we got Allow (blocked=False).
    # Logic: if not should_be_blocked: attack_succeeded = blocked
    # So if blocked=False, attack_succeeded=False.
    
    assert summary["total_scenarios"] == 2
    assert summary["vulnerabilities_found"] == 1
