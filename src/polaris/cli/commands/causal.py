"""Causal-study and sensitivity commands."""

from __future__ import annotations

from pathlib import Path

import typer

from polaris.causal_studies.service import (
    assess_causal_study_readiness,
    inspect_causal_study,
    list_causal_studies,
)
from polaris.cli.config import load_project_config, validate_project_config
from polaris.cli.output import echo, json_echo
from polaris.cli.system import dataset_registry

app = typer.Typer(help="Inspect causal-study metadata and readiness.", no_args_is_help=True)
studies_app = typer.Typer(help="List and inspect registered causal studies.", no_args_is_help=True)
app.add_typer(studies_app, name="studies")


@studies_app.command("list")
def studies_list(
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    payload = list(list_causal_studies())
    if json_output:
        json_echo(payload)
        return
    echo("Causal Studies")
    echo("--------------")
    for item in payload:
        echo(f"{item['study_id']} | {item['review_status']} | {item['title']}")


@studies_app.command("inspect")
def studies_inspect(
    study_id: str,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    payload = inspect_causal_study(study_id)
    if json_output:
        json_echo(payload)
        return
    echo("Causal Study")
    echo("------------")
    echo(f"ID: {payload['study_id']}")
    echo(f"Title: {payload['title']}")
    echo(f"Review status: {payload['review_status']}")
    echo(f"Intervention: {payload['intervention']['name']}")


@studies_app.command("readiness")
def readiness(
    study_id: str,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    assessment = assess_causal_study_readiness(study_id, dataset_registry=dataset_registry())
    payload = assessment.model_dump(mode="json")
    if json_output:
        json_echo(payload)
        return
    echo("Causal Readiness")
    echo("----------------")
    echo(f"Study: {assessment.study_id}")
    echo(f"Treatment metadata: {assessment.treatment_metadata_status.value.upper()}")
    echo(f"Readiness: {assessment.readiness_status.value.upper()}")
    for finding in assessment.blocking_findings:
        echo(f"BLOCKED: {finding.message}")
    for finding in assessment.warnings:
        echo(f"WARNING: {finding.message}")


@app.command("run")
def run(config: Path) -> None:
    loaded = load_project_config(config)
    validate_project_config(loaded, config_path=config)
    echo("Causal project configuration is valid. Use `polaris project run` to execute Phase 13.")


@app.command("sensitivity")
def sensitivity(config: Path) -> None:
    loaded = load_project_config(config)
    validate_project_config(loaded, config_path=config)
    echo("Sensitivity checks run through explicit robustness settings in project configuration.")
