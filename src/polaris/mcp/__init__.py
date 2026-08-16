"""Optional MCP integration boundary for Polaris research capabilities."""

from polaris.mcp.config import MCPServerConfig
from polaris.mcp.server import create_server, run_stdio_server

__all__ = ["MCPServerConfig", "create_server", "run_stdio_server"]
