"""Focused analysis configuration inspection."""

from __future__ import annotations

from pathlib import Path

import typer

from polaris.cli.config import load_project_config, validate_project_config
from polaris.cli.output import echo, json_echo
from polaris.cli.system import dataset_registry
from polaris.projects import plan_research_project

app = typer.Typer(
    help="Inspect the analysis step from a project configuration.",
    no_args_is_help=True,
)


@app.command()
def inspect(
    config: Path,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    loaded = load_project_config(config)
    request = validate_project_config(loaded, config_path=config)
    plan = plan_research_project(request, registry=dataset_registry())
    payload = {
        "procedure": plan.statistical_analysis_step,
        "outcome": loaded.analysis.outcome,
        "predictors": loaded.analysis.predictors,
        "covariates": loaded.analysis.covariates,
        "unit_of_analysis": loaded.analysis.unit_of_analysis,
    }
    if json_output:
        json_echo(payload)
        return
    echo("Analysis")
    echo("--------")
    echo(f"Procedure: {payload['procedure']}")
    echo(f"Outcome: {payload['outcome']}")
    echo(f"Predictors: {', '.join(payload['predictors'])}")
    echo(f"Covariates: {', '.join(payload['covariates']) or 'none'}")
