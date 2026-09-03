"""Export Phase 25 visualization artifacts and plotting-ready data."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from polaris.visualization.errors import VisualizationExportError
from polaris.visualization.models import OutputFormat, OutputReference, VisualizationArtifact
from polaris.visualization.renderers import render_visualization


def export_visualization(
    artifact: VisualizationArtifact,
    *,
    output_directory: Path,
) -> VisualizationArtifact:
    """Export artifact.json, plotting data, and requested render formats."""

    try:
        root = output_directory / artifact.visualization_id
        root.mkdir(parents=True, exist_ok=True)
        outputs: list[OutputReference] = []
        artifact_path = root / "artifact.json"
        artifact_path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
        outputs.append(_reference(OutputFormat.JSON, artifact_path))
        if OutputFormat.CSV in artifact.specification.output_formats:
            csv_path = root / "plot_data.csv"
            _write_csv(csv_path, artifact.plotting_data)
            outputs.append(_reference(OutputFormat.CSV, csv_path))
        if OutputFormat.JSON in artifact.specification.output_formats:
            data_json_path = root / "plot_data.json"
            data_json_path.write_text(
                json.dumps(list(artifact.plotting_data), sort_keys=True, indent=2, allow_nan=False),
                encoding="utf-8",
            )
            outputs.append(_reference(OutputFormat.JSON, data_json_path))
        for fmt in (OutputFormat.PNG, OutputFormat.SVG):
            if fmt in artifact.specification.output_formats:
                figure_path = root / f"figure.{fmt.value}"
                render_visualization(artifact, output_path=figure_path, output_format=fmt)
                outputs.append(_reference(fmt, figure_path))
        return artifact.with_outputs(tuple(outputs))
    except Exception as exc:
        raise VisualizationExportError("failed to export visualization") from exc


def _write_csv(path: Path, rows: tuple[dict[str, Any], ...]) -> None:
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in keys})


def _reference(fmt: OutputFormat, path: Path) -> OutputReference:
    data = path.read_bytes()
    return OutputReference(
        format=fmt,
        path=path.as_posix(),
        checksum_sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
    )
