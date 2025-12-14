from datetime import datetime
from ..core.domain import Policy, GovernanceRequest, GovernanceDecision

class OPAPolicy(Policy):
    """
    Policy that delegates decisions to an Open Policy Agent (OPA) server.
    """
    
    def __init__(
        self,
        url: str,
        policy_path: str,
        timeout: int = 5,
        default_allow: bool = False
    ):
        """
        Args:
            url: OPA server URL (e.g. 'http://localhost:8181')
            policy_path: Path to the policy to evaluate (e.g. 'v1/data/enact/allow')
            timeout: Request timeout in seconds
            default_allow: Decision if OPA is unreachable/errors
        """
        self.url = url.rstrip('/')
        self.policy_path = policy_path.lstrip('/')
        self.timeout = timeout
        self.default_allow = default_allow
        
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        import requests
        
        # Construct OPA input
        opa_input = {
            "input": {
                "agent_id": request.agent_id,
                "tool_name": request.tool_name,
                "function_name": request.function_name,
                "arguments": request.arguments,
                "context": request.context,
                "correlation_id": request.correlation_id,
                "timestamp": str(datetime.now())
            }
        }
        
        endpoint = f"{self.url}/{self.policy_path}"
        
        try:
            response = requests.post(
                endpoint,
                json=opa_input,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # OPA standard response format: {"result": ...}
            # We expect the policy to return boolean or object with 'allow'
            decision_data = result.get("result", {})
            
            if isinstance(decision_data, bool):
                allow = decision_data
                reason = "Allowed by OPA" if allow else "Denied by OPA"
            elif isinstance(decision_data, dict):
                allow = decision_data.get("allow", False)
                reason = decision_data.get("reason", "Denied by OPA")
            else:
                allow = False
                reason = f"Unexpected OPA response format: {decision_data}"
                
            return GovernanceDecision(allow, reason)
            
        except requests.RequestException as e:
            # Check fail-open/closed setting
            reason = f"OPA Error: {str(e)}"
            return GovernanceDecision(self.default_allow, reason)
