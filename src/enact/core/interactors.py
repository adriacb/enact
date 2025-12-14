from typing import List, Optional
from datetime import datetime, timezone
import time
from .domain import GovernanceRequest, GovernanceDecision, Policy, AllowAllPolicy
from .audit import Auditor, AuditLog
from .intent import ValidationPipeline, ToolIntent

class GovernanceEngine:
    """Coordinator that evaluates requests against a policy and validators."""
    
    def __init__(
        self,
        policy: Policy = None,
        auditors: List[Auditor] = None,
        validator: Optional[ValidationPipeline] = None
    ):
        self.policy = policy or AllowAllPolicy()
        self.auditors = auditors or []
        self.validator = validator

    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        """
        Evaluates the request using validators and the configured policy.
        """
        start_time = time.perf_counter()
        
        # 1. Validate Intent (Pre-Execution Check)
        if self.validator:
            # Create intent from request
            # Note: For now we assume default confidence 1.0, 
            # ideally this would come from the request context
            intent = ToolIntent(
                agent_id=request.agent_id,
                tool_name=request.tool_name,
                function_name=request.function_name,
                arguments=request.arguments,
                justification=request.context.get("justification") if request.context else None,
                confidence=request.context.get("confidence", 1.0) if request.context else 1.0
            )
            
            validation_result = self.validator.validate(intent)
            
            if not validation_result.valid:
                # Validation failed
                decision = GovernanceDecision(
                    allow=False,
                    reason=f"Validation failed: {validation_result.reason}"
                )
                self._audit_decision(request, decision, start_time)
                return decision
        
        # 2. Evaluate Policy
        decision = self.policy.evaluate(request)
        
        # 3. Audit
        self._audit_decision(request, decision, start_time)
        
        return decision
        
    def _audit_decision(self, request: GovernanceRequest, decision: GovernanceDecision, start_time: float):
        """Helper to log the audit entry."""
        if not self.auditors:
            return
            
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        audit_entry = AuditLog(
            timestamp=datetime.now(timezone.utc),
            agent_id=request.agent_id,
            tool=request.tool_name,
            function=request.function_name,
            arguments=request.arguments,
            allow=decision.allow,
            reason=decision.reason,
            duration_ms=duration_ms,
            correlation_id=request.correlation_id
        )
        
        for auditor in self.auditors:
            auditor.log(audit_entry)
