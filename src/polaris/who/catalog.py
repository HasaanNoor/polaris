"""WHO GHO acquisition catalog loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from polaris.who.errors import WHOCatalogError


def load_who_acquisition_catalog(catalog_path: str | Path) -> dict[str, Any]:
    """Load the local WHO acquisition catalog without network access."""

    path = Path(catalog_path)
    if not path.exists():
        raise WHOCatalogError(f"WHO acquisition catalog does not exist: {path}")
    with path.open(encoding="utf-8") as file:
        catalog = json.load(file)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("targets"), list):
        raise WHOCatalogError("WHO acquisition catalog must contain a targets list")
    return catalog


def downloaded_targets(catalog: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Return targets with local snapshots recorded by the acquisition catalog."""

    targets = []
    for target in catalog.get("targets", []):
        if target.get("local_snapshot_path") and target.get("selected_who_indicator_id"):
            targets.append(target)
    return tuple(targets)


def target_by_indicator(catalog: dict[str, Any], indicator_id: str) -> dict[str, Any]:
    """Return one catalog target by WHO indicator ID."""

    for target in catalog.get("targets", []):
        if target.get("selected_who_indicator_id") == indicator_id:
            return target
    raise WHOCatalogError(f"WHO indicator not found in acquisition catalog: {indicator_id}")
