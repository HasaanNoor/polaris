"""Local MCP server registration for Polaris."""

from __future__ import annotations

from typing import Any

from polaris.mcp.config import MCPServerConfig, load_config
from polaris.mcp.resources import MCPResourceStore
from polaris.mcp.tools import TOOL_NAMES, MCPToolService


def create_server(config: MCPServerConfig | None = None) -> Any:
    """Create an official MCP SDK server when the optional dependency is installed."""

    active_config = config or MCPServerConfig()
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "The optional 'mcp' package is required to run the Polaris MCP stdio server. "
            "Install Polaris with the 'mcp' extra or install the official MCP Python SDK."
        ) from exc

    resources = MCPResourceStore(active_config)
    tools = MCPToolService(config=active_config, resources=resources)
    server = FastMCP("polaris")

    @server.resource("polaris://datasets")
    def datasets() -> dict[str, Any]:
        return resources.read_resource("polaris://datasets")

    for uri in resources.list_resource_uris():
        if uri == "polaris://datasets":
            continue

        def _reader(resource_uri: str = uri) -> dict[str, Any]:
            return resources.read_resource(resource_uri)

        server.resource(uri)(_reader)

    for name in TOOL_NAMES:

        def _tool(arguments: dict[str, Any] | None = None, tool_name: str = name) -> dict[str, Any]:
            return tools.call_tool(tool_name, arguments or {})

        server.tool(name=name)(_tool)

    return server


def registered_resources(config: MCPServerConfig | None = None) -> tuple[str, ...]:
    return MCPResourceStore(config or MCPServerConfig()).list_resource_uris()


def registered_tools() -> tuple[str, ...]:
    return TOOL_NAMES


def run_stdio_server(config_path: str | None = None) -> None:
    config = load_config(config_path)
    server = create_server(config)
    server.run(transport="stdio")
