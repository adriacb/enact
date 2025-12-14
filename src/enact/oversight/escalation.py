from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

class EscalationLevel(Enum):
    """Escalation levels based on confidence."""
    NONE = "none"           # High confidence, no escalation
    NOTIFY = "notify"       # Medium confidence, notify human
    REVIEW = "review"       # Low confidence, require review
    APPROVAL = "approval"   # Very low confidence, require approval

@dataclass
class ConfidenceThresholds:
    """Thresholds for confidence-based escalation."""
    high: float = 0.9      # Above this: no escalation
    medium: float = 0.7    # Above this: notify only
    low: float = 0.5       # Above this: review required
    # Below low: approval required

@dataclass
class EscalationDecision:
    """Result of escalation evaluation."""
    level: EscalationLevel
    confidence: float
    requires_human: bool
    message: str

class ConfidenceEscalation:
    """
    Confidence-based escalation system.
    
    Automatically escalates to human oversight when agent
    confidence falls below configured thresholds.
    """
    
    def __init__(
        self,
        thresholds: Optional[ConfidenceThresholds] = None,
        notify_callback: Optional[Callable] = None,
        review_callback: Optional[Callable] = None,
        approval_callback: Optional[Callable] = None
    ):
        """
        Args:
            thresholds: Confidence thresholds for escalation
            notify_callback: Called when notification needed
            review_callback: Called when review needed
            approval_callback: Called when approval needed
        """
        self.thresholds = thresholds or ConfidenceThresholds()
        self.notify_callback = notify_callback
        self.review_callback = review_callback
        self.approval_callback = approval_callback
    
    def evaluate(
        self,
        confidence: float,
        agent_id: str,
        tool_name: str,
        function_name: str,
        context: Optional[dict] = None
    ) -> EscalationDecision:
        """
        Evaluate if escalation is needed based on confidence.
        
        Args:
            confidence: Agent's confidence score (0.0 - 1.0)
            agent_id: Agent making the request
            tool_name: Tool being accessed
            function_name: Function being called
            context: Additional context
            
        Returns:
            EscalationDecision with level and requirements
        """
        # Validate confidence
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
        
        # Determine escalation level
        if confidence >= self.thresholds.high:
            level = EscalationLevel.NONE
            requires_human = False
            message = "High confidence - proceeding"
            
        elif confidence >= self.thresholds.medium:
            level = EscalationLevel.NOTIFY
            requires_human = False
            message = "Medium confidence - human notified"
            
            if self.notify_callback:
                self.notify_callback(agent_id, tool_name, function_name, confidence, context)
        
        elif confidence >= self.thresholds.low:
            level = EscalationLevel.REVIEW
            requires_human = True
            message = "Low confidence - human review required"
            
            if self.review_callback:
                self.review_callback(agent_id, tool_name, function_name, confidence, context)
        
        else:
            level = EscalationLevel.APPROVAL
            requires_human = True
            message = "Very low confidence - human approval required"
            
            if self.approval_callback:
                self.approval_callback(agent_id, tool_name, function_name, confidence, context)
        
        return EscalationDecision(
            level=level,
            confidence=confidence,
            requires_human=requires_human,
            message=message
        )
    
    def set_thresholds(self, thresholds: ConfidenceThresholds):
        """Update confidence thresholds."""
        self.thresholds = thresholds
    
    def get_thresholds(self) -> ConfidenceThresholds:
        """Get current thresholds."""
        return self.thresholds
