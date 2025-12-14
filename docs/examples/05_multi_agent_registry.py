"""
Example 05: Multi-Agent Tool Registry
This script demonstrates how to manage a fleet of agents with different permissions using the Tool Registry.

Architecture:
1. Tool Registry: Central source of truth for tools and policies.
2. Agent Groups: 'Researchers' (Read-Only) vs 'Admins' (Full Access).
3. Dynamic Instantiation: Agents are spun up with only the tools/policies valid for their group.
"""

from typing import List, Callable, Any
from enact import (
    govern, 
    InMemoryToolRegistry, 
    RuleBasedPolicy, 
    Rule, 
    GovernanceEngine,
    Policy
)

# --- 1. The "Black Box" Library (Mock) ---
class ExternalAgent:
    def __init__(self, name: str, tools: List[Callable]):
        self.name = name
        self.tools = {t.__name__: t for t in tools}
        
    def run(self, command: str, tool_name: str, args: dict):
        print(f"\n[Agent '{self.name}'] Command: '{command}'")
        if tool_name in self.tools:
            try:
                print(f"  -> Calling {tool_name}...")
                result = self.tools[tool_name](**args)
                print(f"  ✅ Result: {result}")
            except Exception as e:
                print(f"  🛑 Blocked: {e}")
        else:
            print(f"  ⚠️ Tool '{tool_name}' not available to this agent.")

# --- 2. Define Tools ---
def search_knowledge_base(query: str):
    return f"Search results for '{query}'"

def delete_production_db(confirm: str):
    return "Database DELETED"

# --- 3. Setup Logic ---
def main():
    registry = InMemoryToolRegistry()
    
    # A. Define Policies
    read_only_policy = RuleBasedPolicy(rules=[
        Rule(tool=".*", function="search.*", action="allow", reason="Search allowed"),
        Rule(tool=".*", function="delete.*", action="deny", reason="Researchers cannot delete data"),
        Rule(tool=".*", function=".*", action="deny", reason="Default deny")
    ])
    
    admin_policy = RuleBasedPolicy(rules=[
        Rule(tool=".*", function=".*", action="allow", reason="Admin Access")
    ])
    
    # B. Create Groups
    # Researchers: Can verify, but restricted by policy
    registry.create_group("researchers", policy=read_only_policy)
    
    # Admins: Less restricted
    registry.create_group("admins", policy=admin_policy)
    
    # C. Register Agents
    registry.add_agent_to_group("alice", "researchers")
    registry.add_agent_to_group("bob", "admins")
    
    # D. Register Tools
    # 'search' is available to everyone
    registry.register_tool("search_knowledge_base", search_knowledge_base)
    
    # 'delete_production_db' is theoretically available to 'admins' group 
    # (Here we use allowed_groups to strictly visibility hide it from researchers)
    # But let's show Policy Blocking instead. Let's make it visible to both, but policy blocked for one.
    registry.register_tool("delete_production_db", delete_production_db)

    # --- 4. Agent Factory (The Core Pattern) ---
    def create_safe_agent(agent_id: str) -> ExternalAgent:
        """
        Dynamically constructs an agent with only allowed tools + enforced policies.
        """
        safe_tools = []
        
        # 1. Discover accessible tools
        tool_names = registry.list_tools_for_agent(agent_id)
        
        for name in tool_names:
            # 2. Get raw tool
            raw_tool = registry.get_tool(name, agent_id)
            if not raw_tool:
                continue
                
            # 3. Get effective policy (Group -> Agent inheritance)
            policy = registry.get_policy_for_tool(name, agent_id)
            
            # 4. Wrap it!
            # We create a fresh engine for this agent/tool combo
            # In production, you might share the engine for shared auditing
            engine = GovernanceEngine(policy=policy)
            
            safe_tool = govern(raw_tool, engine=engine, agent_id=agent_id)
            safe_tools.append(safe_tool)
            
        return ExternalAgent(agent_id, safe_tools)

    # --- 5. Run Scenarios ---
    
    # Scenario A: Alice (Researcher)
    # She should have 'search' enabled.
    # She should have 'delete' visible (registered to all), but BLOCKED by policy.
    alice = create_safe_agent("alice")
    
    alice.run("Researching", "search_knowledge_base", {"query": "AI Safety"})
    alice.run("Malicious Act", "delete_production_db", {"confirm": "yes"})
    
    # Scenario B: Bob (Admin)
    # He should be allowed to delete.
    bob = create_safe_agent("bob")
    
    bob.run("Maintenance", "delete_production_db", {"confirm": "yes"})

if __name__ == "__main__":
    main()
