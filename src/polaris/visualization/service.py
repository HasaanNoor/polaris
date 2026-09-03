"""Public service API for Phase 25 visualizations."""

from pathlib import Path

from polaris.visualization.builders import build_visualization
from polaris.visualization.exporters import export_visualization
from polaris.visualization.models import VisualizationArtifact, VisualizationSpecification


def create_visualization(
    *,
    specification: VisualizationSpecification,
    source_artifact: object,
    data_artifact: object | None = None,
    comparison_artifacts: tuple[object, ...] = (),
    output_directory: Path | None = None,
) -> VisualizationArtifact:
    artifact = build_visualization(
        specification=specification,
        source_artifact=source_artifact,
        data_artifact=data_artifact,
        comparison_artifacts=comparison_artifacts,
    )
    if output_directory is not None:
        return export_visualization(artifact, output_directory=output_directory)
    return artifact
