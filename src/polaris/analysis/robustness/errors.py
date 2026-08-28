"""Focused errors for causal robustness analysis."""

from polaris.analysis.errors import AnalysisCompatibilityError


class RobustnessSpecificationError(AnalysisCompatibilityError):
    """Raised when a robustness specification is malformed."""


class InvalidRobustnessVariantError(RobustnessSpecificationError):
    """Raised when a requested robustness variant is invalid."""


class IncompatibleVariantError(RobustnessSpecificationError):
    """Raised when a variant is incompatible with the baseline causal design."""


class InsufficientRobustnessSampleError(RobustnessSpecificationError):
    """Raised when a robustness variant leaves too little usable sample."""


class InvalidPlaceboSpecificationError(RobustnessSpecificationError):
    """Raised when a placebo diagnostic is not explicitly defensible."""


class RobustnessExecutionError(AnalysisCompatibilityError):
    """Raised when robustness execution fails outside expected variant failures."""
