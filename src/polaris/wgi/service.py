"""Public WGI governance panel API."""

from pathlib import Path

from polaris.wgi.acquisition import download_wgi_data
from polaris.wgi.export import export_wgi_governance_panel
from polaris.wgi.models import WGIGovernancePanel, WGIPanelExportResult, WGISnapshotReference
from polaris.wgi.panel import build_wgi_governance_panel


def build_panel_from_local_or_download(
    *,
    raw_root: str | Path = "data/raw",
    acquire_if_missing: bool = False,
) -> WGIGovernancePanel:
    """Build the WGI panel, optionally acquiring official snapshots first."""

    snapshots: tuple[WGISnapshotReference, ...] | None = None
    if acquire_if_missing:
        snapshots = download_wgi_data(raw_root=raw_root)
    return build_wgi_governance_panel(raw_root=raw_root, snapshots=snapshots)


__all__ = [
    "WGIGovernancePanel",
    "WGIPanelExportResult",
    "build_panel_from_local_or_download",
    "build_wgi_governance_panel",
    "download_wgi_data",
    "export_wgi_governance_panel",
]
