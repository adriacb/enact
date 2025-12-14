from typing import List, Optional
from datetime import datetime, timezone
import time
from .domain import GovernanceRequest, GovernanceDecision, Policy, AllowAllPolicy
from .audit import Auditor, AuditLog
from .intent import ValidationPipeline, ToolIntent

# Type checking imports to avoid circular deps if any, though here it is fine
from ..safety.rate_limiter import RateLimiter
from ..reliability.circuit_breaker import CircuitBreaker
from ..oversight.approval import ApprovalWorkflow
from ..oversight.kill_switch import KillSwitch

class GovernanceEngine:
    """Coordinator that evaluates requests against a policy and validators."""
    
    def __init__(
        self,
        policy: Policy = None,
        auditors: List[Auditor] = None,
        validator: Optional[ValidationPipeline] = None,
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        approval_workflow: Optional[ApprovalWorkflow] = None,
        kill_switch: Optional[KillSwitch] = None
    ):
        self.policy = policy or AllowAllPolicy()
        self.auditors = auditors or []
        self.validator = validator
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker
        self.approval_workflow = approval_workflow
        self.kill_switch = kill_switch

    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        """
        Evaluates the request using validators and the configured policy.
        """
        start_time = time.perf_counter()
        
        # 0. Kill Switch (Immediate Logic)
        if self.kill_switch and self.kill_switch.is_active():
            decision = GovernanceDecision(
                allow=False,
                reason=f"Kill Switch Active: {self.kill_switch.reason}"
            )
            self._audit_decision(request, decision, start_time)
            return decision

        # 0.1 Circuit Breaker (Availability)
        if self.circuit_breaker and self.circuit_breaker.is_open(request.tool_name):
            decision = GovernanceDecision(
                allow=False,
                reason="Circuit Breaker Open"
            )
            self._audit_decision(request, decision, start_time)
            return decision

        # 0.2 Rate Limiter (Throttling)
        if self.rate_limiter:
            if not self.rate_limiter.check_limit(request.agent_id, request.tool_name):
                decision = GovernanceDecision(
                    allow=False,
                    reason="Rate limit exceeded"
                )
                self._audit_decision(request, decision, start_time)
                return decision

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
        
        # 3. Approval Workflow (If allowed by policy but might need approval)
        if decision.allow and self.approval_workflow:
            if self.approval_workflow.requires_approval(
                request.agent_id, 
                request.tool_name, 
                request.function_name, 
                request.arguments
            ):
                # Check if already approved
                if not self.approval_workflow.is_approved(
                    request.agent_id,
                    request.tool_name,
                    request.function_name,
                    request.arguments
                ):
                    # Request approval
                    approval_req = self.approval_workflow.request_approval(
                        agent_id=request.agent_id,
                        tool_name=request.tool_name,
                        function_name=request.function_name,
                        arguments=request.arguments,
                        justification=request.context.get("justification") if request.context else None
                    )
                    decision = GovernanceDecision(
                        allow=False,
                        reason=f"Operation requires approval. Request ID: {approval_req.id}"
                    )
        
        # 4. Audit
        self._audit_decision(request, decision, start_time)
        
        # 5. Record Success/Failure for Circuit Breaker (Basic Heuristic)
        # Note: True success/failure comes from tool execution, which is outside engine.
        # But we can at least record that we ALLOWED it. 
        # Ideally, we need a feedback loop 'engine.record_result(...)'.
        # For now, CB only opens on external signal or we assume 'allow' = attempted.
        # Enact's proxy wrapper (ReliableToolProxy) handles the recording of actual tool exceptions.
        # So we don't do it here.
        
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
