"""Domain exceptions for deterministic statistical analysis."""


class StatisticalAnalysisError(Exception):
    """Base error for Phase 4 statistical analysis."""

    def __init__(
        self,
        message: str,
        *,
        dataset_id: str | None = None,
        method: str | None = None,
        variable_id: str | None = None,
        sample_size: int | None = None,
    ) -> None:
        super().__init__(message)
        self.dataset_id = dataset_id
        self.method = method
        self.variable_id = variable_id
        self.sample_size = sample_size


class AnalysisCompatibilityError(StatisticalAnalysisError):
    """Raised when a specification cannot run against ingested data."""


class UnsupportedAnalysisMethodError(AnalysisCompatibilityError):
    """Raised when Phase 4 does not support the requested method."""


class AnalysisNotReadyError(StatisticalAnalysisError):
    """Raised when an ingestion result is not analysis-ready."""


class InsufficientSampleError(AnalysisCompatibilityError):
    """Raised when the complete-case sample is too small."""


class VariableNotFoundError(AnalysisCompatibilityError):
    """Raised when a requested variable is absent."""


class VariableTypeError(AnalysisCompatibilityError):
    """Raised when a variable has an incompatible manifest type."""


class RegressionExecutionError(StatisticalAnalysisError):
    """Raised when regression execution fails unexpectedly."""


class DiagnosticExecutionError(StatisticalAnalysisError):
    """Raised when diagnostic execution fails unexpectedly."""
