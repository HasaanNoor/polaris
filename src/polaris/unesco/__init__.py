"""UNESCO UIS education panel integration."""

from polaris.unesco.export import export_unesco_education_panel, unesco_education_panel_manifest
from polaris.unesco.panel import build_unesco_education_panel, default_selected_indicators
from polaris.unesco.profiling import profile_all_downloaded_datasets, profile_unesco_indicator

__all__ = [
    "build_unesco_education_panel",
    "default_selected_indicators",
    "export_unesco_education_panel",
    "profile_all_downloaded_datasets",
    "profile_unesco_indicator",
    "unesco_education_panel_manifest",
]
