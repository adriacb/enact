from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

@dataclass
class GovernanceRequest:
    """Represents a request to access a tool."""
    agent_id: str
    tool_name: str
    function_name: str
    arguments: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

@dataclass
class GovernanceDecision:
    """Represents the decision made by the governance layer."""
    allow: bool
    reason: str
    modified_arguments: Optional[Dict[str, Any]] = None

class Policy(Protocol):
    """Interface for governance policies."""
    
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        """Evaluates a request and returns a decision."""
        ...

class AllowAllPolicy(Policy):
    """A default policy that allows everything."""
    
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        return GovernanceDecision(allow=True, reason="AllowAllPolicy: Default allow")
