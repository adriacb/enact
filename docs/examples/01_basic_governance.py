"""
Example 01: Basic Governance
This script demonstrates how to set up a simple tool registry and govern it with basic rules.
"""

from enact import (
    InMemoryToolRegistry, 
    GovernanceEngine, 
    RuleBasedPolicy, 
    Rule, 
    GovernanceRequest
)

def query_database(query: str):
    """A mock restricted tool."""
    return f"Database result for: {query}"

def check_health():
    """A mock public tool."""
    return "System OK"

def main():
    # 1. Setup Registry
    registry = InMemoryToolRegistry()
    registry.register_tool("db_tool", query_database)
    registry.register_tool("health_check", check_health)

    # 2. Define Policy
    # - Allow health_check for everyone
    # - Allow db_tool only for 'admin' user
    policy = RuleBasedPolicy(rules=[
        Rule(tool="health_check", function="*", action="allow", reason="Public health check"),
        Rule(tool="db_tool", function="*", action="allow", reason="Admin Access", agent_id="admin"),
        Rule(tool=".*", function=".*", action="deny", reason="Default deny") 
    ])

    # 3. Setup Engine
    engine = GovernanceEngine(policy=policy)

    # 4. Simulate Requests
    
    # Scenario A: Admin accessing DB (Should Succeed)
    print("\n--- Scenario A: Admin accessing DB ---")
    request_a = GovernanceRequest(
        agent_id="admin",
        tool_name="db_tool",
        function_name="query_database",
        arguments={"query": "SELECT * FROM users"}
    )
    decision_a = engine.evaluate(request_a)
    print(f"Decision: {decision_a.allow} (Reason: {decision_a.reason})")
    
    if decision_a.allow:
        tool = registry.get_tool("db_tool", "admin")
        print(f"Result: {tool('SELECT * FROM users')}")

    # Scenario B: Guest accessing DB (Should Fail)
    print("\n--- Scenario B: Guest accessing DB ---")
    request_b = GovernanceRequest(
        agent_id="guest",
        tool_name="db_tool",
        function_name="query_database",
        arguments={"query": "DROP TABLE users"}
    )
    decision_b = engine.evaluate(request_b)
    print(f"Decision: {decision_b.allow} (Reason: {decision_b.reason})")

if __name__ == "__main__":
    main()
