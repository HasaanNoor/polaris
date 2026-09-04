"""Report commands."""

from __future__ import annotations

import json

import typer

from polaris.cli.errors import CLIResourceNotFoundError
from polaris.cli.output import echo, json_echo
from polaris.cli.system import DEFAULT_OUTPUT_ROOT

app = typer.Typer(help="Inspect generated project reports.", no_args_is_help=True)


@app.command("generate")
def generate(project_id: str) -> None:
    root = DEFAULT_OUTPUT_ROOT / project_id / "report"
    if not root.exists():
        raise CLIResourceNotFoundError(f"Report directory not found for project: {project_id}")
    echo(f"Report already generated in {root}")


@app.command("inspect")
def inspect(
    report_id: str,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    for project_file in DEFAULT_OUTPUT_ROOT.glob("project_*/project.json"):
        payload = json.loads(project_file.read_text(encoding="utf-8"))
        if payload.get("project_provenance", {}).get("report_id") == report_id:
            report_dir = project_file.parent / "report"
            files = sorted(str(path) for path in report_dir.glob("report.*"))
            out = {"report_id": report_id, "project_id": payload["project_id"], "files": files}
            if json_output:
                json_echo(out)
            else:
                echo("Report")
                echo("------")
                echo(f"ID: {report_id}")
                echo(f"Project: {payload['project_id']}")
                for file in files:
                    echo(file)
            return
    raise CLIResourceNotFoundError(f"Report not found: {report_id}")
