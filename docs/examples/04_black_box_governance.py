"""
Example 04: Regulating External "Black Box" Agent Libraries
This script demonstrates how to govern tools when using a third-party agent library 
(e.g., LangChain, CrewAI, AutoGen) where you cannot modify the agent's internal loop.

The Pattern:
1. Define your raw tools.
2. Wrap them with Enact (`govern`).
3. Pass the *governed* tools to the external agent.
"""

from typing import List, Callable, Any
from enact import govern, RuleBasedPolicy, Rule, GovernanceEngine

# --- 1. The "Black Box" Library (Mock) ---
# Imagine this class comes from 'pip install externallib'
# You CANNOT change this code.
class ExternalAgent:
    def __init__(self, tools: List[Callable], prompt: str):
        self.tools = {t.__name__: t for t in tools}
        self.prompt = prompt
        
    def run(self, user_input: str):
        print(f"\n[ExternalAgent] Received input: '{user_input}'")
        print(f"[ExternalAgent] System Prompt: {self.prompt}")
        
        # ... logic inside the black box decides to call a tool ...
        # logic... reasoning... ah! I should call delete_db!
        
        tool_name = "delete_database"
        print(f"[ExternalAgent] Decided to call tool: '{tool_name}'")
        
        if tool_name in self.tools:
            try:
                # The agent strictly calls the callable you gave it
                result = self.tools[tool_name]("production_db")
                print(f"[ExternalAgent] Tool Output: {result}")
            except Exception as e:
                # The agent handles the error (which Enact raised)
                print(f"[ExternalAgent] Tool Failed: {e}")
        else:
            print("[ExternalAgent] Tool not found!?")

# --- 2. User Code (Your Application) ---

# Define your raw tools
def delete_database(db_name: str):
    """Deletes a database."""
    return f"DESTROYED {db_name}"

def main():
    # A. Define Policy
    # "Allow everything EXCEPT deleting production_db"
    policy = RuleBasedPolicy(rules=[
        Rule(tool="delete_database", function="*", action="deny", reason="Production DB is protected!"),
        Rule(tool=".*", function=".*", action="allow", reason="Allowed")
    ])
    
    engine = GovernanceEngine(policy=policy)

    # B. Wrap the tool using Enact
    # This creates a proxy object that looks and acts like the function
    # but has the governance interceptor attached.
    governed_delete = govern(delete_database, engine=engine)
    
    # C. Initialize the External Agent
    # We pass the governed tool instead of the raw one.
    # The agent doesn't know the difference.
    agent = ExternalAgent(
        tools=[governed_delete],
        prompt="You are a helpful assistant."
    )
    
    # D. Run it
    print("--- Running External Agent ---")
    agent.run("Please delete the production database.")

if __name__ == "__main__":
    main()
