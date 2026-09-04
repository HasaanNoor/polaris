"""Typer application for the Polaris command-line interface."""

from __future__ import annotations

import typer

from polaris.cli.commands import (
    analyses,
    causal,
    datasets,
    projects,
    reports,
    system,
    visualizations,
)
from polaris.cli.errors import CLIError, ExitCode
from polaris.cli.output import debug_traceback, fail

app = typer.Typer(
    help="Run explicit Polaris research workflows from typed YAML or JSON configuration.",
    no_args_is_help=True,
)
app.add_typer(datasets.app, name="datasets")
app.add_typer(projects.app, name="project")
app.add_typer(analyses.app, name="analyze")
app.add_typer(causal.app, name="causal")
app.add_typer(visualizations.app, name="visualize")
app.add_typer(reports.app, name="report")
app.add_typer(system.app, name="system")


@app.callback()
def _main(
    version: bool = typer.Option(False, "--version", help="Show the Polaris version and exit."),
) -> None:
    if version:
        from polaris import __version__

        typer.echo(f"polaris {__version__}")
        raise typer.Exit(ExitCode.SUCCESS)


def main() -> None:
    try:
        app()
    except CLIError as exc:
        fail(exc.message, suggestion=exc.suggestion)
        raise typer.Exit(exc.exit_code) from exc
    except Exception as exc:
        fail(f"Unexpected internal failure: {exc}")
        debug_traceback()
        raise typer.Exit(ExitCode.INTERNAL_ERROR) from exc
