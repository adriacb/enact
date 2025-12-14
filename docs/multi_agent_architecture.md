# Multi-Agent Governance Architecture

This document explains the architecture implemented in `examples/05_multi_agent_registry.py`.

## Conceptual Flow

The system uses a **Central Registry** to define permissions, but enforces them via **Distributed Proxies** wrapped around tools injected into agents.

```mermaid
graph TD
    %% --- Configuration Phase ---
    subgraph Registry ["Central Tool Registry"]
        direction TB
        Tool_DB["Tool: DeleteDB"]
        Tool_Search["Tool: Search"]
        
        subgraph Groups
            Group_R["Group: Researchers"]
            Group_A["Group: Admins"]
        end
        
        subgraph Policies
            Policy_R["Policy: Read-Only"]
            Policy_A["Policy: Admin-Access"]
        end
        
        Group_R -.->|Use| Policy_R
        Group_A -.->|Use| Policy_A
    end

    %% --- Provisioning Phase ---
    subgraph Factory ["Agent Factory"]
        Logic["create_safe_agent(agent_id)"]
    end

    Registry -->|Provide Tool & Policy| Factory

    %% --- Runtime Phase ---
    subgraph Runtime
        subgraph Alice_Scope ["Alice (Researcher)"]
            Alice["Agent Alice"]
            Proxy_A["Enact Proxy"]
        end

        subgraph Bob_Scope ["Bob (Admin)"]
            Bob["Agent Bob"]
            Proxy_B["Enact Proxy"]
        end
    end

    Factory -- Creates --> Proxy_A
    Factory -- Creates --> Proxy_B

    %% --- Execution Flow ---
    Alice -->|"Call delete_db"| Proxy_A
    Proxy_A -->|"Check Read-Only Policy"| Block["🛑 BLOCKED"]

    Bob -->|"Call delete_db"| Proxy_B
    Proxy_B -->|"Check Admin Policy"| Allow["✅ ALLOWED"]
    Allow -->|Execute| Tool_DB

    %% Styling
    style Registry fill:#f9f9f9,stroke:#333
    style Factory fill:#e1f5fe,stroke:#0277bd
    style Block fill:#ffcdd2,stroke:#c62828
    style Allow fill:#c8e6c9,stroke:#2e7d32
```

## Key Components

1.  **Registry**: The single source of truth. It knows that "Alice" belongs to "Researchers" and that "Researchers" use the `ReadOnlyPolicy`.
2.  **Factory**: The code that bridges configuration and runtime. It fetches the *specific* policy for Alice regarding `delete_db` and instantiates a `GovernanceEngine` just for that tool.
3.  **Proxies**: The `ExternalAgent` (Alice) doesn't hold the real `delete_db` function. It holds an `Enact` wrapper. When Alice tries to call it, the wrapper runs the policy check locally.

---

# Rule & Policy Reference

This section details how to define explicit Rules for use in a `RuleBasedPolicy`.

## The `Rule` Object

A `Rule` defines a pattern to match against a tool execution request.

### Fields
*   **tool** (`str`): Regex pattern to match the tool name (e.g., `delete_file`, `db_.*`).
*   **function** (`str`): Regex pattern to match the function name (e.g., `execute_.*`, `*`).
*   **agent_id** (`str`): Regex pattern to match the agent ID calling the tool (e.g., `admin`, `user_.*`, `*`). *Default: `*`*.
*   **action** (`str`): `"allow"` or `"deny"`.
*   **reason** (`str`): Human-readable explanation for the audit log.

## Defining Policies

### 1. In Python (Programmatic)

Use this for dynamic policies or when defining rules alongside code.

```python
from enact import RuleBasedPolicy, Rule

policy = RuleBasedPolicy(rules=[
    # Allow specific tool for specific agent
    Rule(
        tool="database_tool",
        function="delete_table",
        agent_id="admin_bob",  # Only Bob can do this
        action="allow",
        reason="Bob is the DBO"
    ),
    # Allow read-only for everyone else
    Rule(
        tool="database_tool",
        function="read_.*",
        action="allow",  # agent_id defaults to "*"
        reason="Public Read Access"
    ),
    # Deny everything else (Best Practice)
    Rule(
        tool=".*",
        function=".*",
        action="deny",
        reason="Default Deny"
    )
])
```

### 2. In YAML (Configuration)

Use this for externalizing policy from code, easier for non-devs to review. Load with `PolicyLoader.load("policy.yaml")`.

```yaml
default_allow: false
rules:
  - tool: "database_tool"
    function: "delete_table"
    agent_id: "admin_bob"
    action: "allow"
    reason: "Bob is the DBO"

  - tool: "database_tool"
    function: "read_.*"
    action: "allow"
    reason: "Public Read Access"

  - tool: ".*"
    function: ".*"
    action: "deny"
    reason: "Default Deny"
```

### 3. In JSON (API/Web)

Use this for receiving policies from APIs or frontends. Load with `PolicyLoader.load("policy.json")`.

```json
{
  "default_allow": false,
  "rules": [
    {
      "tool": "database_tool",
      "function": "delete_table",
      "agent_id": "admin_bob",
      "action": "allow",
      "reason": "Bob is the DBO"
    },
    {
      "tool": "database_tool",
      "function": "read_.*",
      "action": "allow",
      "reason": "Public Read Access"
    },
    {
      "tool": ".*",
      "function": ".*",
      "action": "deny",
      "reason": "Default Deny"
    }
  ]
}
```
