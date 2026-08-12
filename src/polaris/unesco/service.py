"""Public synchronous UNESCO education panel API."""

from __future__ import annotations

from pathlib import Path

from polaris.unesco.export import export_unesco_education_panel
from polaris.unesco.models import UNESCOEducationPanel, UNESCOEducationPanelExportResult
from polaris.unesco.panel import build_unesco_education_panel
from polaris.unesco.profiling import profile_unesco_indicator

__all__ = [
    "UNESCOEducationPanel",
    "UNESCOEducationPanelExportResult",
    "build_unesco_education_panel",
    "export_unesco_education_panel",
    "profile_unesco_indicator",
]


def build_and_export_unesco_education_panel(
    *,
    raw_root: str | Path = "data/raw/unesco",
    output_dir: str | Path = "examples/unesco",
) -> UNESCOEducationPanelExportResult:
    panel = build_unesco_education_panel(raw_root=raw_root)
    return export_unesco_education_panel(panel=panel, output_dir=output_dir)
