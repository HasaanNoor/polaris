"""Shared CLI system paths and local registries."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from polaris import __version__
from polaris.registry import DatasetRegistry, load_registry

PROJECT_ROOT = Path.cwd()
CATALOG_DIR = PROJECT_ROOT / "catalog" / "datasets"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "projects"
CAUSAL_REGISTRY_DIR = PROJECT_ROOT / "data" / "causal_studies"


def dataset_registry() -> DatasetRegistry:
    return load_registry(CATALOG_DIR)


def package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def system_info_payload() -> dict[str, object]:
    import platform

    return {
        "polaris_version": __version__,
        "python_version": platform.python_version(),
        "cli": True,
        "yaml": package_available("yaml"),
        "visualization": package_available("matplotlib"),
        "mcp": package_available("mcp"),
        "provider_backed_reasoning": False,
        "output_root": str(DEFAULT_OUTPUT_ROOT),
    }
