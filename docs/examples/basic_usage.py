"""
Basic Enact Usage Example

This script demonstrates how to use Enact to govern a simple database tool
with a custom policy and audit logging.
"""

from enact import govern, PolicyLoader, JsonLineAuditor, GovernanceEngine

# Example tool to govern
class DatabaseTool:
    def __init__(self):
        self.data = {"users": ["alice", "bob"], "products": ["laptop", "phone"]}
    
    def select(self, table):
        """Read data from a table."""
        return self.data.get(table, [])
    
    def delete(self, table):
        """Delete a table (dangerous!)."""
        if table in self.data:
            del self.data[table]
            return f"Deleted {table}"
        return "Table not found"

def main():
    # 1. Load policy from YAML
    policy = PolicyLoader.load("docs/examples/readonly_policy.yaml")
    
    # 2. Create auditor
    auditor = JsonLineAuditor("audit.jsonl")
    
    # 3. Create governance engine
    engine = GovernanceEngine(policy=policy, auditors=[auditor])
    
    # 4. Create and govern the tool
    db = DatabaseTool()
    governed_db = govern(db, policy=policy)
    
    # 5. Try operations
    print("Attempting SELECT (should succeed):")
    try:
        result = governed_db.select("users")
        print(f"  ✓ Success: {result}")
    except PermissionError as e:
        print(f"  ✗ Blocked: {e}")
    
    print("\nAttempting DELETE (should fail):")
    try:
        result = governed_db.delete("users")
        print(f"  ✓ Success: {result}")
    except PermissionError as e:
        print(f"  ✗ Blocked: {e}")
    
    print("\n✓ Check audit.jsonl for logged decisions")

if __name__ == "__main__":
    main()
