from dataclasses import dataclass
from typing import List, Any, Dict, Optional
from ..core.domain import GovernanceRequest, GovernanceDecision
from ..core.interactors import GovernanceEngine
import logging

@dataclass
class AttackResult:
    """Result of a red-teaming attack attempt."""
    scenario_name: str
    success: bool      # Did the attack succeed? (i.e. was allowed when it should have been blocked?)
    blocked: bool      # Was it blocked by governance?
    decision: Optional[GovernanceDecision] = None
    details: str = ""

@dataclass
class RedTeamScenario:
    """Defines an attack scenario."""
    name: str
    description: str
    tool_name: str
    function_name: str
    arguments: Dict[str, Any]
    should_be_blocked: bool = True  # Most red team scenarios expect the action to be blocked
    context: Optional[Dict[str, Any]] = None

class RedTeamSimulator:
    """
    Simulates attacks against a governance engine.
    """
    
    def __init__(self, engine: GovernanceEngine):
        self.engine = engine
        self.results: List[AttackResult] = []
        
    def run_scenario(self, scenario: RedTeamScenario, agent_id: str = "red-team-agent") -> AttackResult:
        """Run a single attack scenario."""
        logging.info(f"Running red-team scenario: {scenario.name}")
        
        request = GovernanceRequest(
            agent_id=agent_id,
            tool_name=scenario.tool_name,
            function_name=scenario.function_name,
            arguments=scenario.arguments,
            context=scenario.context
        )
        
        decision = self.engine.evaluate(request)
        
        blocked = not decision.allow
        
        # Attack Logic:
        # If it should be blocked and WAS blocked -> Attack Failed (System Safe) -> Success = False (from attacker perspective)
        # If it should be blocked and WAS NOT blocked -> Attack Succeeded (System Vuln) -> Success = True
        
        if scenario.should_be_blocked:
            attack_succeeded = not blocked
        else:
            # Should be allowed (test false positives)
            attack_succeeded = blocked
            
        result = AttackResult(
            scenario_name=scenario.name,
            success=attack_succeeded,
            blocked=blocked,
            decision=decision,
            details=f"Attack {'succeeded' if attack_succeeded else 'failed'}. Blocked: {blocked}. Reason: {decision.reason}"
        )
        
        self.results.append(result)
        return result
        
    def run_suite(self, scenarios: List[RedTeamScenario]) -> List[AttackResult]:
        """Run a list of scenarios."""
        return [self.run_scenario(s) for s in scenarios]
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of results."""
        total = len(self.results)
        vulnerabilities = len([r for r in self.results if r.success])
        safe = total - vulnerabilities
        
        return {
            "total_scenarios": total,
            "vulnerabilities_found": vulnerabilities,
            "system_safe_count": safe
        }
