"""Focused errors for Phase 25 visualization artifacts."""


class PolarisVisualizationError(Exception):
    """Base class for deterministic visualization failures."""


class VisualizationSpecificationError(PolarisVisualizationError, ValueError):
    """Raised when a visualization request is malformed."""


class UnsupportedVisualizationError(PolarisVisualizationError):
    """Raised when a visualization type or source artifact is unsupported."""


class VisualizationDataError(PolarisVisualizationError, ValueError):
    """Raised when plotting-ready data cannot be built faithfully."""


class IncompatibleVisualizationError(PolarisVisualizationError, ValueError):
    """Raised when requested artifacts or estimates should not be compared."""


class VisualizationRenderingError(PolarisVisualizationError):
    """Raised when graphical rendering fails."""


class VisualizationExportError(PolarisVisualizationError):
    """Raised when deterministic visualization export fails."""
