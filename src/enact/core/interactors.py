from typing import List
from .domain import GovernanceRequest, GovernanceDecision, Policy, AllowAllPolicy

class GovernanceEngine:
    """Coordinator that evaluates requests against a policy."""
    
    def __init__(self, policy: Policy = None):
        self.policy = policy or AllowAllPolicy()

    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        """
        Evaluates the request using the configured policy.
        """
        # In a more complex scenario, this might aggregate multiple policies.
        # For now, it delegates to the single injected policy.
        return self.policy.evaluate(request)
