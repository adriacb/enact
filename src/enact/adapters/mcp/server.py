import asyncio
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, CallToolRequest, CallToolResult, TextContent

from ...core.interactors import GovernanceEngine
from ...core.domain import GovernanceRequest

class MCPGovernanceServer:
    """
    A Middleware MCP Server that governs access to an upstream MCP server.
    """
    def __init__(self, name: str, upstream_client: Any, engine: GovernanceEngine, agent_id: str = "default-agent"):
        """
        Args:
            name: The name of this middleware server.
            upstream_client: A client connection to the real MCP server. 
                             (Must support list_tools and call_tool)
            engine: The governance engine to enforce policies.
            agent_id: The identity of the agent.
        """
        self.name = name
        self.upstream = upstream_client
        self.engine = engine
        self.agent_id = agent_id
        self.app = Server(name)
        
        self._setup_handlers()

    def _setup_handlers(self):
        """Register the tool interceptors with the internal server."""
        self.app.list_tools()(self.handle_list_tools)
        self.app.call_tool()(self.handle_call_tool)

    async def handle_list_tools(self) -> List[Tool]:
        """Handler for listing tools."""
        # Fetch tools from upstream
        # In a real implementation, we would inspect the upstream capabilities.
        # For now, we assume simple proxying.
        tools = await self.upstream.list_tools()
        
        # Future: Filter tools based on policy (e.g. hide 'delete_db' entirely)
        return tools

    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for calling tools."""
        # 1. Create Governance Request
        request = GovernanceRequest(
            agent_id=self.agent_id,
            tool_name="upstream", # We might want to be more specific if possible
            function_name=name,
            arguments=arguments
        )
        
        # 2. Check Policy
        decision = self.engine.evaluate(request)
        
        if not decision.allow:
            return [TextContent(
                type="text",
                text=f"Governance Error: {decision.reason}"
            )]

        # 3. Use Modified Arguments if applicable
        final_args = decision.modified_arguments if decision.modified_arguments else arguments

        # 4. Call Upstream
        # Note: The return type of upstream.call_tool needs to match MCP expectation
        result = await self.upstream.call_tool(name, final_args)
        return result

    async def run_stdio(self):
        """Runs the server over stdio."""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )
