"""Visualization commands."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from polaris.cli.config import load_project_config, validate_project_config
from polaris.cli.errors import CLIResourceNotFoundError
from polaris.cli.output import echo, json_echo
from polaris.cli.system import DEFAULT_OUTPUT_ROOT, dataset_registry
from polaris.projects import plan_research_project

app = typer.Typer(help="Create or inspect explicit project visualizations.", no_args_is_help=True)


@app.command("create")
def create(config: Path, dry_run: bool = typer.Option(True, "--dry-run/--execute")) -> None:
    loaded = load_project_config(config)
    request = validate_project_config(loaded, config_path=config)
    plan = plan_research_project(request, registry=dataset_registry())
    if dry_run:
        echo("Visualization plan")
        echo(f"Project: {plan.project_id}")
        echo(f"Specifications: {len(request.visualization.specifications)}")
        return
    echo("Visualizations are generated as part of `polaris project run`.")


@app.command("list")
def list_visualizations(
    project_id: str,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    payload = _project(project_id)
    ids = payload.get("project_provenance", {}).get("visualization_artifact_ids", [])
    if json_output:
        json_echo(ids)
        return
    echo("Visualizations")
    echo("--------------")
    for item in ids:
        echo(item)


@app.command("inspect")
def inspect(visualization_id: str) -> None:
    for project_file in DEFAULT_OUTPUT_ROOT.glob("project_*/project.json"):
        payload = json.loads(project_file.read_text(encoding="utf-8"))
        ids = payload.get("project_provenance", {}).get("visualization_artifact_ids", [])
        if visualization_id in ids:
            echo(f"Visualization: {visualization_id}")
            echo(f"Project: {payload['project_id']}")
            return
    raise CLIResourceNotFoundError(f"Visualization not found: {visualization_id}")


def _project(project_id: str) -> dict:
    path = DEFAULT_OUTPUT_ROOT / project_id / "project.json"
    if not path.exists():
        raise CLIResourceNotFoundError(f"Project not found: {project_id}")
    return json.loads(path.read_text(encoding="utf-8"))
