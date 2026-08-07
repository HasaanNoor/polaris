"""Structured errors for Phase 13 research-project orchestration."""

from __future__ import annotations

from polaris.projects.models import ResearchStage


class ResearchProjectError(Exception):
    """Base class for project orchestration failures."""


class DatasetResolutionError(ResearchProjectError):
    """Raised when an explicit dataset input cannot be resolved."""


class ResearchProjectExecutionError(ResearchProjectError):
    """Raised by callers that prefer exception-based failed-stage handling."""

    def __init__(self, message: str, *, stage: ResearchStage, original_error: Exception) -> None:
        super().__init__(message)
        self.stage = stage
        self.original_error = original_error
