"""Research diagnostic helpers for Phase 25 visualization specifications."""

from polaris.visualization.models import VisualizationSpecification, VisualizationType


def missingness_by_variable_spec(
    *,
    source_artifact_id: str,
    selected_variables: tuple[str, ...],
) -> VisualizationSpecification:
    return VisualizationSpecification(
        visualization_type=VisualizationType.MISSINGNESS_BY_VARIABLE,
        source_artifact_id=source_artifact_id,
        selected_variables=selected_variables,
    )


def country_year_coverage_spec(
    *,
    source_artifact_id: str,
    selected_variables: tuple[str, ...],
    selected_entities: tuple[str, ...] = (),
) -> VisualizationSpecification:
    return VisualizationSpecification(
        visualization_type=VisualizationType.COUNTRY_YEAR_COVERAGE,
        source_artifact_id=source_artifact_id,
        selected_variables=selected_variables,
        selected_entities=selected_entities,
    )
