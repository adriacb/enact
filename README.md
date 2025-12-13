# Enact: AI Agent Governance Layer

Enact is a lightweight governance layer for AI Agents. It intercepts tool execution to enforce granular access control policies without modifying your agent's core logic.

## Key Features

1.  **Agent Agnostic**: Works with LangChain, LlamaIndex, Vanilla OpenAI, or any python-based agent.
2.  **Immutable Agents**: Wraps tools *before* they reach the agent. No code changes to the agent class.
3.  **Unified Governance**: Supports both local Python objects and [Model Context Protocol (MCP)](https://modelcontextprotocol.io) tools.
4.  **Configurable**: Define policies in Python or via YAML/JSON.

## Installation

```bash
uv pip install enact
# or
pip install .
```

## Quick Start

### 1. Governed Python Objects (Local)

Wrap your existing tool classes seamlessly.

```python
from enact import govern, Policy, GovernanceRequest, GovernanceDecision

class DatabaseTool:
    def delete_table(self, name):
        print(f"Deleting {name}...")

# Define a simple policy
class SafeMode(Policy):
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        if "delete" in request.function_name:
            return GovernanceDecision(allow=False, reason="Safety violation")
        return GovernanceDecision(allow=True, reason="Allowed")

# Governance happens here
db = DatabaseTool()
safe_db = govern(db, SafeMode())

# Agent uses safe_db as if it were the original
safe_db.delete_table("users")  # Raises PermissionError
```

### 2. Governance Middleware for MCP

Enforce policies on remote tools served via the Model Context Protocol.

```python
from enact.adapters.mcp import MCPGovernanceServer
from enact.config import PolicyLoader
import asyncio

# ... connect to upstream_client ...

# Load policy from file
engine = GovernanceEngine(policy=PolicyLoader.load("policy.yaml"))

# Run the Middleware Server
server = MCPGovernanceServer(
    name="governance-proxy", 
    upstream_client=upstream_client, 
    engine=engine
)
# await server.run_stdio()
```

### 3. YAML Configuration

Define complex rules without writing code coverage.

**policy.yaml**
```yaml
default_allow: false
rules:
  - tool: "database"
    function: "select_.*"
    action: "allow"
    reason: "Read-only access permitted"
  - tool: "*"
    function: "*"
    action: "deny"
    reason: "Implicit deny"
```

## Documentation
- [Writing Custom Policies](docs/guides/custom_policies.md)
- [Architecture Concept](docs/concept.md)

## Architecture

Enact uses a **Proxy Pattern** for local objects and a **Middleware Pattern** for MCP.

`Agent` -> `[ Enact Governance Layer ]` -> `[ Real Tool / MCP Server ]`

This ensures that the Agent always sees a standard interface, while Enact handles the security.
