# Project Concept: AI Agent Tool Governance

## Overview
This project aims to establish a governance layer for AI Agents, specifically focusing on managing and controlling their access to tools. As AI agents become more autonomous and capable of interacting with external systems (databases, APIs, etc.), a robust mechanism is needed to define, restrict, and audit these interactions.

## Core Idea
The central premise is to decouple the agent's definition from the raw tool implementation, introducing a governance layer that mediates tool access.

An agent is typically defined as:
```python
Agent(prompt="...", tools=[AccessBBDD, SendEmail])
```

However, simply passing a list of tools is insufficient for complex environments. We need to answer questions like:
- *Which* data can this agent access within the database?
- *Who* authorized this agent to send emails?
- *When* can this tool be used?

## Key Features

### 1. Granular Access Control
Different agents may utilize the same underlying tool implementation but with drastically different permissions.
- **Agent A (Admin)**: Uses `AccessBBDD` with read/write permissions on all tables.
- **Agent B (Viewer)**: Uses `AccessBBDD` but the governance layer restricts it to read-only access on specific tables.

### 2. Tool Abstraction & MCP Integration
The governance layer abstracts the source of the tools. Tools can be:
- **Local Code**: Functions or classes defined within the same codebase.
- **MCP Servers**: Tools exposed via the Model Context Protocol (MCP) from remote or separate processes.

The agent should not care where the tool lives; it interacts with the governed interface.

### 3. Unified Governance Policy
The project will provide a way to define policies that dictate:
- **Identity**: Who the agent is acting on behalf of.
- **Scope**: What specific actions or parameters are allowed for a given tool.
- **Auditability**: Logging and tracking tool usage across different agents.

## Architecture: The Governance Proxy

To satisfy the constraint that **Agents must not be modified**, we introduce the **Governance Proxy** pattern. This layer sits transparently between the Agent and the actual Tools.

### Design Principles
1.  **Agent Agnosticism**: The component works with any agent framework (LangChain, LlamaIndex, Vanilla OpenAI, etc.).
2.  **Immutability**: The Agent's definition remains `Agent(tools=[...])`. The "tools" passed in are simply wrapped or proxied versions.
3.  **Transparency**: The Agent believes it is interacting directly with the original tools.

### Implementation Patterns

#### Pattern A: Object Proxy (Local Wrappers)
For frameworks where tools are passed as Python objects (e.g., `tools=[AccessDDBB()]`):
- The Governance Layer wraps the `AccessDDBB` instance.
- It returns a **Proxy Object** that matches the interface (signatures, docstrings, Pydantic models) of the original tool.
- When the Agent invokes a method on the proxy, the Governance Layer intercepts the call, evaluates the policy, and then delegates to the real object if allowed.

*Example Usage:*
```python
# Instead of: Agent(tools=[AccessDDBB()])
# We use:
governed_db = Enact.govern(AccessDDBB(), policy=read_only_policy)
Agent(tools=[governed_db])
```

#### Pattern B: MCP Interceptor (Client-Server)
For frameworks that fetch tools from an MCP Server (e.g., `list_tools()`):
- The Governance Layer acts as a **Middleware MCP Server**.
- It connects to the upstream "Real" MCP Server.
- It exposes a filtered/modified list of tools to the Agent.
- When the Agent requests to execute a tool, the request hits the Governance Layer first, which checks compliance before forwarding the request to the upstream server.

### Visual Flow
Agent -> [ Governance Layer (Policy Engine) ] -> [ Real Tool / MCP Server ]
