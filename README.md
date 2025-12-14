# Enact: AI Agent Governance Layer

Enact is a lightweight governance layer for AI Agents. It intercepts tool execution to enforce granular access control policies without modifying your agent's core logic.

## Key Features

1.  **Agent Agnostic**: Works with LangChain, LlamaIndex, Vanilla OpenAI, or any python-based agent.
2.  **Immutable Agents**: Wraps tools *before* they reach the agent. No code changes to the agent class.
3.  **Unified Governance**: Supports both local Python objects and [Model Context Protocol (MCP)](https://modelcontextprotocol.io) tools.
4.  **Configurable**: Define policies in Python or via YAML/JSON.
5.  **Audit Logging**: Track all governance decisions with built-in JSON logging.

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

### 4. Audit Logging

Track all governance decisions for compliance and observability.

```python
from enact import govern, PolicyLoader, JsonLineAuditor, GovernanceEngine

# Create auditor
auditor = JsonLineAuditor("audit.jsonl")

# Create engine with policy and auditor
policy = PolicyLoader.load("policy.yaml")
engine = GovernanceEngine(policy=policy, auditors=[auditor])

# Use with govern (note: currently you need to pass engine separately)
# All decisions are logged to audit.jsonl
```

**Remote Logging with HTTPAuditor:**
```python
from enact import HTTPAuditor

# Send logs to external service
http_auditor = HTTPAuditor(
    url="https://your-logging-service.com/api/logs",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    timeout=5
)

engine = GovernanceEngine(policy=policy, auditors=[http_auditor])
```

**Syslog Integration:**
```python
from enact import SyslogAuditor

syslog_auditor = SyslogAuditor(
    host='syslog.example.com',
    port=514,
    facility=16  # local0
)
```

**AWS CloudWatch Logs:**
```python
from enact import CloudWatchAuditor

# Requires: pip install enact[cloud]
cloudwatch_auditor = CloudWatchAuditor(
    log_group='/enact/governance',
    log_stream='production',
    region='us-east-1'
)
```

**Log Format:**
```json
{"timestamp": "2025-12-13T22:50:00Z", "agent_id": "agent1", "tool": "db", "function": "query", "allow": true, "reason": "Allowed", "duration_ms": 0.5}
```

### 5. Tool Registry

Centralized management of tools with agent groups and policy inheritance.

```python
from enact import InMemoryToolRegistry

# Create registry
registry = InMemoryToolRegistry()

# Register tools with access control
registry.register_tool("admin_db", admin_db, allowed_agents=["admin"])
registry.register_tool("public_api", api_tool)  # No restrictions

# Create agent groups
registry.create_group("developers", policy=dev_policy)
registry.add_agent_to_group("alice", "developers")
registry.add_agent_to_group("bob", "developers")

# Register tools for groups
registry.register_tool("dev_db", dev_db, allowed_groups=["developers"])

# Get tool for agent (with access check)
tool = registry.get_tool("dev_db", "alice")  # Returns tool
tool = registry.get_tool("admin_db", "alice")  # Returns None

# List accessible tools
tools = registry.list_tools_for_agent("alice")  # ["public_api", "dev_db"]
```

**Policy Inheritance:** tool-specific → agent-specific → group policy

## Examples

Check out [docs/examples/](docs/examples/) for:
- **[readonly_policy.yaml](docs/examples/readonly_policy.yaml)** - Example read-only database policy
- **[basic_usage.py](docs/examples/basic_usage.py)** - Complete usage example with audit logging

## Documentation
- [Writing Custom Policies](docs/guides/custom_policies.md)
- [Tool Registry Guide](docs/guides/tool_registry.md)
- [Audit Logging Guide](docs/guides/audit_logging.md)
- [Safety & Reliability Guide](docs/guides/safety_reliability.md)
- [Human Oversight Guide](docs/guides/human_oversight.md)
- [Intent Validation Guide](docs/guides/intent_validation.md)
- [Advanced Features Guide](docs/guides/advanced_features.md)
- [Continuous Evaluation Guide](docs/guides/continuous_evaluation.md)
- [Integration Master Guide](docs/guides/integration_master_guide.md)
- [Architecture Concept](docs/concept.md)

## Architecture

Enact uses a **Proxy Pattern** for local objects and a **Middleware Pattern** for MCP.

`Agent` -> `[ Enact Governance Layer ]` -> `[ Real Tool / MCP Server ]`

This ensures that the Agent always sees a standard interface, while Enact handles the security.
