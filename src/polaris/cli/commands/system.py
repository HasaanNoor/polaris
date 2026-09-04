"""System inspection commands."""

from __future__ import annotations

import typer

from polaris.cli.output import echo, json_echo
from polaris.cli.system import system_info_payload

app = typer.Typer(help="Inspect local Polaris environment.", no_args_is_help=True)


@app.command("info")
def info(
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    payload = system_info_payload()
    if json_output:
        json_echo(payload)
        return
    echo("Polaris System")
    echo("--------------")
    echo(f"Version: {payload['polaris_version']}")
    echo(f"Python: {payload['python_version']}")
    echo(f"YAML support: {payload['yaml']}")
    echo(f"Visualization support: {payload['visualization']}")
    echo(f"MCP support: {payload['mcp']}")
    echo(f"Provider-backed reasoning: {payload['provider_backed_reasoning']}")
    echo(f"Output root: {payload['output_root']}")
