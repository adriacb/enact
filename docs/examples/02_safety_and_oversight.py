"""
Example 02: Safety & Oversight
This script demonstrates advance safety patterns:
- Rate Limiting
- Circuit Breaking
- Human Approval Workflow
- Kill Switch
"""

import time
from enact import (
    GovernanceEngine, AllowAllPolicy, GovernanceRequest,
    RateLimiter, CircuitBreaker, ApprovalWorkflow, KillSwitch
)

def risky_operation():
    """A tool that might fail or be dangerous."""
    print("  -> Performing risky operation...")
    return "Success"

def main():
    # 1. Configure Oversight Components
    
    # Simple rate limiter: 2 requests per minute
    rate_limiter = RateLimiter(max_requests=2, window_seconds=60)
    
    # Approval workflow for "deploy" actions
    approval = ApprovalWorkflow()
    
    # Global Kill Switch
    kill_switch = KillSwitch()

    # 2. Setup Engine with Safety Features
    engine = GovernanceEngine(
        policy=AllowAllPolicy(), # Policy allows, but safety might block
        rate_limiter=rate_limiter,
        approval_workflow=approval,
        kill_switch=kill_switch
    )

    # --- Scenario 1: Rate Limiting ---
    print("\n--- Scenario 1: Rate Limiting ---")
    req = GovernanceRequest("bot", "api", "call", {})
    
    for i in range(3):
        decision = engine.evaluate(req)
        print(f"Request {i+1}: Allowed={decision.allow} ({decision.reason})")

    # --- Scenario 2: Human Approval ---
    print("\n--- Scenario 2: Human Approval ---")
    deploy_req = GovernanceRequest("bot", "deploy", "prod", {})
    
    # First attempt - should be paused for approval
    d1 = engine.evaluate(deploy_req)
    print(f"Attempt 1: {d1.reason}") 
    
    # Mock Human Approval
    print("  [Human Operator]: Approving request...")
    approval.approve(d1.reason.split("ID: ")[1].strip()) # Extract ID from reason string
    
    # Second attempt - should pass
    d2 = engine.evaluate(deploy_req)
    print(f"Attempt 2: Allowed={d2.allow}")

    # --- Scenario 3: Kill Switch ---
    print("\n--- Scenario 3: Emergency Kill Switch ---")
    print("  [System]: Activating Kill Switch!")
    kill_switch.activate("Security Breach Detected")
    
    decision_k = engine.evaluate(req)
    print(f"Request: Allowed={decision_k.allow} ({decision_k.reason})")

if __name__ == "__main__":
    main()
