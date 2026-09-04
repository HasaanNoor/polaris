"""CLI-focused errors and exit-code mapping."""

from __future__ import annotations

from enum import IntEnum

import click


class ExitCode(IntEnum):
    SUCCESS = 0
    CONFIGURATION_ERROR = 2
    EXECUTION_FAILURE = 3
    RESOURCE_NOT_FOUND = 4
    INTERNAL_ERROR = 1


class CLIError(click.ClickException):
    exit_code = ExitCode.INTERNAL_ERROR

    def __init__(self, message: str, *, suggestion: str | None = None) -> None:
        if suggestion:
            message = f"{message}\nSuggested action: {suggestion}"
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion


class CLIConfigurationError(CLIError):
    exit_code = ExitCode.CONFIGURATION_ERROR


class CLIResourceNotFoundError(CLIError):
    exit_code = ExitCode.RESOURCE_NOT_FOUND


class CLIExecutionError(CLIError):
    exit_code = ExitCode.EXECUTION_FAILURE


class CLIOutputError(CLIError):
    exit_code = ExitCode.INTERNAL_ERROR
