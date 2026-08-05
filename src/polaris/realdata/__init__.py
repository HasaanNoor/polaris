"""Phase 11 validation for real downloaded provider datasets."""

from polaris.realdata.discovery import discover_real_datasets
from polaris.realdata.runner import run_real_dataset_validation

__all__ = [
    "discover_real_datasets",
    "run_real_dataset_validation",
]
