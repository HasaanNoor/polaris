"""Errors for Phase 19 reasoning evaluation."""


class ReasoningEvaluationError(Exception):
    """Base error for reasoning evaluation failures."""


class BenchmarkExecutionError(ReasoningEvaluationError):
    """Raised when a benchmark suite cannot be executed."""
