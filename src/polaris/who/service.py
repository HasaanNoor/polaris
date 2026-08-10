"""Public synchronous WHO panel API."""

from __future__ import annotations

from pathlib import Path

from polaris.who.catalog import load_who_acquisition_catalog, target_by_indicator
from polaris.who.export import export_who_health_panel
from polaris.who.models import WHOHealthPanel, WHOIndicatorProfile, WHOPanelExportResult
from polaris.who.panel import build_who_health_panel
from polaris.who.profiling import profile_who_indicator


def profile_indicator_from_catalog(
    *,
    catalog_path: str | Path,
    indicator_id: str,
) -> WHOIndicatorProfile:
    """Profile one local WHO indicator identified by the acquisition catalog."""

    catalog = load_who_acquisition_catalog(catalog_path)
    return profile_who_indicator(target=target_by_indicator(catalog, indicator_id))


__all__ = [
    "WHOHealthPanel",
    "WHOIndicatorProfile",
    "WHOPanelExportResult",
    "build_who_health_panel",
    "export_who_health_panel",
    "profile_indicator_from_catalog",
]
