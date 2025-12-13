import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from enact.adapters.mcp.server import MCPGovernanceServer
from enact.core.domain import AllowAllPolicy, GovernanceRequest, GovernanceDecision, Policy
from mcp.types import TextContent

# --- Mocks ---
class MockUpstreamClient:
    def __init__(self):
        self.list_tools = AsyncMock(return_value=[])
        self.call_tool = AsyncMock(return_value=[
            TextContent(type="text", text="Upstream Result")
        ])

# --- Tests ---

@pytest.mark.asyncio
async def test_mcp_server_proxies_allowed_calls():
    # Setup
    upstream = MockUpstreamClient()
    engine = MagicMock()
    # Mock engine to allow
    engine.evaluate.return_value = GovernanceDecision(allow=True, reason="ok")
    
    server = MCPGovernanceServer("test-server", upstream, engine)
    
    # Action: invoke the handler directly
    result = await server.handle_call_tool("my_tool", {"arg": 1})
    
    # Assert
    upstream.call_tool.assert_awaited_with("my_tool", {"arg": 1})
    assert len(result) == 1
    assert result[0].text == "Upstream Result"

@pytest.mark.asyncio
async def test_mcp_server_blocks_forbidden_calls():
    # Setup
    upstream = MockUpstreamClient()
    engine = MagicMock()
    # Mock engine to block
    engine.evaluate.return_value = GovernanceDecision(allow=False, reason="Forbidden")
    
    server = MCPGovernanceServer("test-server", upstream, engine)
    
    # Action
    result = await server.handle_call_tool("dangerous_tool", {})
    
    # Assert
    upstream.call_tool.assert_not_called()
    assert len(result) == 1
    assert "Governance Error: Forbidden" in result[0].text
