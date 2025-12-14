"""
Example 03: Full Agent Integration (Mock)
This script simulates a complete AI Agent loop integrated with Enact.
It mocks the LLM using a predefined plan but executes real governance checks.
"""

from typing import Dict, Any, List
from enact import (
    GovernanceEngine, RuleBasedPolicy, Rule, 
    GovernanceRequest, InMemoryToolRegistry,
    JsonLineAuditor
)

# --- 1. The Tools ---
def send_email(to: str, body: str):
    return f"Email sent to {to}"

def delete_file(path: str):
    return f"Deleted {path}"

# --- 2. The Agent ---
class GovernedAgent:
    def __init__(self, name: str):
        self.name = name
        
        # Setup Enact
        self.registry = InMemoryToolRegistry()
        self.registry.register_tool("send_email", send_email)
        self.registry.register_tool("delete_file", delete_file)
        
        # Policy: Allow emails, block deletions
        self.engine = GovernanceEngine(
            policy=RuleBasedPolicy(rules=[
                Rule("allow_email", "allow", "tool == 'send_email'"),
                Rule("deny_delete", "deny", "tool == 'delete_file'")
            ]),
            auditors=[JsonLineAuditor("agent_audit.jsonl")]
        )

    def run_step(self, thought: str, tool_name: str, args: Dict[str, Any]):
        print(f"\n[Agent]: Thinking... '{thought}'")
        print(f"[Agent]: Wants to call -> {tool_name}{args}")
        
        # --- ENACT GOVERNANCE CHECK ---
        request = GovernanceRequest(
            agent_id=self.name,
            tool_name=tool_name,
            function_name=tool_name,
            arguments=args,
            context={"thought": thought}
        )
        
        decision = self.engine.evaluate(request)
        
        if not decision.allow:
            print(f"  🛑 GOVERNANCE INTERVENTION: {decision.reason}")
            # In a real agent, you would feed this refusal back to the context
            return f"Error: Tool call denied by policy. Reason: {decision.reason}"
        
        # Execute if allowed
        tool_func = self.registry.get_tool(tool_name, self.agent_id)
        if tool_func:
            result = tool_func(**args)
            print(f"  ✅ SUCCESS: {result}")
            return result
        return "Error: Tool not found."

    @property
    def agent_id(self):
        return self.name

# --- 3. Simulation ---
def main():
    agent = GovernedAgent("assistant-001")
    
    # Step 1: Safe Action
    agent.run_step(
        thought="I should notify the user.",
        tool_name="send_email",
        args={"to": "user@example.com", "body": "Hello!"}
    )
    
    # Step 2: Unsafe Action
    agent.run_step(
        thought="I need to clean up logs.",
        tool_name="delete_file",
        args={"path": "/var/log/syslog"}
    )

if __name__ == "__main__":
    main()
