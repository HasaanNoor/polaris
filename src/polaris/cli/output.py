"""Output helpers for human-readable and JSON CLI responses."""

from __future__ import annotations

import json
import sys
from typing import Any

import typer


def echo(message: str = "", *, quiet: bool = False, err: bool = False) -> None:
    if not quiet:
        typer.echo(message, err=err)


def json_echo(payload: Any) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def progress(message: str, *, quiet: bool = False, json_output: bool = False) -> None:
    if not quiet:
        typer.echo(message, err=json_output)


def fail(message: str, *, suggestion: str | None = None) -> None:
    typer.echo(message, err=True)
    if suggestion:
        typer.echo(f"Suggested action: {suggestion}", err=True)


def debug_traceback() -> None:
    import traceback

    traceback.print_exc(file=sys.stderr)
