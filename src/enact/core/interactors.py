from typing import List
from datetime import datetime, timezone
import time
from .domain import GovernanceRequest, GovernanceDecision, Policy, AllowAllPolicy
from .audit import Auditor, AuditLog

class GovernanceEngine:
    """Coordinator that evaluates requests against a policy."""
    
    def __init__(self, policy: Policy = None, auditors: List[Auditor] = None):
        self.policy = policy or AllowAllPolicy()
        self.auditors = auditors or []

    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        """
        Evaluates the request using the configured policy.
        """
        start_time = time.perf_counter()
        
        # Evaluate policy
        decision = self.policy.evaluate(request)
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Audit the decision
        if self.auditors:
            audit_entry = AuditLog(
                timestamp=datetime.now(timezone.utc),
                agent_id=request.agent_id,
                tool=request.tool_name,
                function=request.function_name,
                arguments=request.arguments,
                allow=decision.allow,
                reason=decision.reason,
                duration_ms=duration_ms
            )
            
            for auditor in self.auditors:
                auditor.log(audit_entry)
        
        return decision
