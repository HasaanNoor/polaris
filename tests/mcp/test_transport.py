from __future__ import annotations

import pytest

import polaris
from polaris.mcp.server import create_server, registered_resources, registered_tools


def test_normal_import_does_not_launch_mcp():
    assert polaris.__version__


def test_registered_resources_and_tools_are_discoverable():
    resources = registered_resources()
    tools = registered_tools()

    assert "polaris://datasets" in resources
    assert "polaris://catalogs/who/variables" in resources
    assert "run_research_project" in tools
    assert "run_analysis" in tools


def test_stdio_server_requires_optional_sdk_when_not_installed():
    with pytest.raises(RuntimeError, match="optional 'mcp' package"):
        create_server()
