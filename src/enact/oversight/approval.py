from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Callable, Set
from enum import Enum
import uuid

class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class ApprovalRequest:
    """Represents a request for human approval."""
    id: str
    agent_id: str
    tool_name: str
    function_name: str
    arguments: Dict
    justification: Optional[str] = None
    risk_level: str = "MEDIUM"
    created_at: datetime = field(default_factory=datetime.now)
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

class ApprovalWorkflow:
    """
    Manages human approval workflows for high-risk operations.
    
    Allows configuring which tools/operations require approval
    and provides mechanisms for requesting and granting approval.
    """
    
    def __init__(
        self,
        high_risk_tools: Optional[Set[str]] = None,
        high_risk_functions: Optional[Set[str]] = None,
        approval_callback: Optional[Callable] = None
    ):
        """
        Args:
            high_risk_tools: Set of tool names requiring approval
            high_risk_functions: Set of function patterns requiring approval (regex)
            approval_callback: Optional callback to notify when approval needed
        """
        self.high_risk_tools = high_risk_tools or set()
        self.high_risk_functions = high_risk_functions or set()
        self.approval_callback = approval_callback
        
        # Pending approvals
        self.pending: Dict[str, ApprovalRequest] = {}
        
        # Approval history
        self.history: list = []
    
    def requires_approval(
        self,
        agent_id: str,
        tool_name: str,
        function_name: str,
        arguments: Dict
    ) -> bool:
        """
        Check if operation requires approval.
        
        Args:
            agent_id: Agent requesting the operation
            tool_name: Tool being accessed
            function_name: Function being called
            arguments: Function arguments
            
        Returns:
            True if approval required, False otherwise
        """
        # Check if tool is high-risk
        if tool_name in self.high_risk_tools:
            return True
        
        # Check if function matches high-risk patterns
        import re
        for pattern in self.high_risk_functions:
            if re.match(pattern, function_name):
                return True
        
        return False
    
    def request_approval(
        self,
        agent_id: str,
        tool_name: str,
        function_name: str,
        arguments: Dict,
        justification: Optional[str] = None,
        risk_level: str = "MEDIUM"
    ) -> ApprovalRequest:
        """
        Request human approval for an operation.
        
        Args:
            agent_id: Agent requesting approval
            tool_name: Tool to be accessed
            function_name: Function to be called
            arguments: Function arguments
            justification: Reason for the operation
            risk_level: Risk level (LOW/MEDIUM/HIGH/CRITICAL)
            
        Returns:
            ApprovalRequest object
        """
        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            tool_name=tool_name,
            function_name=function_name,
            arguments=arguments,
            justification=justification,
            risk_level=risk_level
        )
        
        self.pending[request.id] = request
        
        # Trigger callback if provided
        if self.approval_callback:
            self.approval_callback(request)
        
        return request
    
    def approve(
        self,
        request_id: str,
        approver: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Approve a pending request.
        
        Args:
            request_id: ID of the request to approve
            approver: ID of the person approving
            notes: Optional approval notes
            
        Returns:
            True if approved, False if request not found
        """
        if request_id not in self.pending:
            return False
        
        request = self.pending[request_id]
        request.status = ApprovalStatus.APPROVED
        request.approver = approver
        request.approved_at = datetime.now()
        
        # Move to history
        self.history.append(request)
        del self.pending[request_id]
        
        return True
    
    def reject(
        self,
        request_id: str,
        approver: str,
        reason: str
    ) -> bool:
        """
        Reject a pending request.
        
        Args:
            request_id: ID of the request to reject
            approver: ID of the person rejecting
            reason: Reason for rejection
            
        Returns:
            True if rejected, False if request not found
        """
        if request_id not in self.pending:
            return False
        
        request = self.pending[request_id]
        request.status = ApprovalStatus.REJECTED
        request.approver = approver
        request.approved_at = datetime.now()
        request.rejection_reason = reason
        
        # Move to history
        self.history.append(request)
        del self.pending[request_id]
        
        return True
    
    def get_status(self, request_id: str) -> Optional[ApprovalStatus]:
        """Get status of an approval request."""
        if request_id in self.pending:
            return self.pending[request_id].status
        
        # Check history
        for req in self.history:
            if req.id == request_id:
                return req.status
        
        return None
    
    def get_pending_requests(self) -> list:
        """Get all pending approval requests."""
        return list(self.pending.values())
    
    def clear_pending(self):
        """Clear all pending requests (use with caution)."""
        self.pending.clear()

    def is_approved(self, agent_id: str, tool_name: str, function_name: str, arguments: Dict) -> bool:
        """Check if a matching request has been approved."""
        # Check history for approved requests with matching parameters
        # In a real system, you might want to expire approvals or check timestamps
        for req in self.history:
            if (req.status == ApprovalStatus.APPROVED and
                req.agent_id == agent_id and
                req.tool_name == tool_name and
                req.function_name == function_name and
                req.arguments == arguments):
                return True
        return False
