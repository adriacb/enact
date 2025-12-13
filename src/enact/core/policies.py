import re
from dataclasses import dataclass, field
from typing import List, Optional
from .domain import Policy, GovernanceRequest, GovernanceDecision

@dataclass
class Rule:
    """
    A single governance rule.
    
    Attributes:
        tool: Regex pattern to match knowledge of tool name (e.g. "database", "api_.*", "*")
        function: Regex pattern to match function name (e.g. "delete_.*", "*")
        action: "allow" or "deny"
        reason: Explanation for the decision
    """
    tool: str
    function: str
    action: str  # "allow" | "deny"
    reason: str

class RuleBasedPolicy(Policy):
    """
    A policy that evaluates a request against a list of ordered rules.
    The first matching rule determines the outcome.
    If no rule matches, it falls back to a default action (default: deny).
    """
    def __init__(self, rules: List[Rule], default_allow: bool = False):
        self.rules = rules
        self.default_allow = default_allow

    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        for rule in self.rules:
            if self._matches(rule, request):
                is_allowed = (rule.action.lower() == "allow")
                return GovernanceDecision(
                    allow=is_allowed,
                    reason=f"Matched rule: {rule.reason}"
                )
        
        # No rule matched
        if self.default_allow:
            return GovernanceDecision(allow=True, reason="Default allow (no rule matched)")
        else:
            return GovernanceDecision(allow=False, reason="Default deny (no rule matched)")

    def _matches(self, rule: Rule, request: GovernanceRequest) -> bool:
        """Checks if the request matches the rule's patterns."""
        # Convert glob-like '*' to regex '.*' if user provided simple wildcards, 
        # or assume strictly regex? 
        # For simplicity and UX, let's treat the inputs as Regex patterns directly,
        # but maybe safeguard '*' to act as '.*' if it's exactly just '*'.
        
        tool_pattern = rule.tool
        if tool_pattern == "*":
            tool_pattern = ".*"
            
        function_pattern = rule.function
        if function_pattern == "*":
            function_pattern = ".*"

        # Check Tool Name
        if not re.fullmatch(tool_pattern, request.tool_name):
            return False
            
        # Check Function Name
        if not re.fullmatch(function_pattern, request.function_name):
            return False

        return True
