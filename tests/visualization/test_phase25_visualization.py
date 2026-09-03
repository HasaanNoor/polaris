from pathlib import Path

import pytest

from polaris.analysis.causal import CausalAnalysisRequest, run_causal_analysis
from polaris.analysis.models import AnalysisRequest
from polaris.analysis.robustness import RobustnessVariant, RobustnessVariantType, analyze_robustness
from polaris.analysis.service import run_analysis
from polaris.mcp.tools import MCPToolService
from polaris.visualization import (
    OutputFormat,
    VisualizationSpecification,
    VisualizationType,
    build_visualization,
    export_visualization,
)
from polaris.visualization.errors import VisualizationSpecificationError
from polaris.visualization.models import PanelDiagnosticKind
from tests.analysis.causal.conftest import causal_spec, synthetic_causal_ingestion
from tests.analysis.conftest import analysis_ingestion as _analysis_ingestion_fixture
from tests.analysis.conftest import analysis_manifest as _analysis_manifest_fixture
from tests.analysis.helpers import make_spec
from tests.analysis.panel.conftest import panel_ingestion as _panel_ingestion_fixture
from tests.analysis.panel.conftest import panel_spec


@pytest.fixture
def causal_ingestion(tmp_path: Path):
    return synthetic_causal_ingestion(tmp_path)


@pytest.fixture
def analysis_ingestion(tmp_path: Path):
    return _analysis_ingestion_fixture.__wrapped__(
        tmp_path,
        _analysis_manifest_fixture.__wrapped__(),
    )


@pytest.fixture
def panel_ingestion(tmp_path: Path):
    return _panel_ingestion_fixture.__wrapped__(tmp_path)


def _baseline(ingestion):
    return run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=ingestion,
            causal_specification=causal_spec(),
        )
    )


def _robustness_spec(baseline, variants=None):
    from polaris.analysis.robustness import RobustnessSpecification

    return RobustnessSpecification(
        specification_id="robustness_spec",
        baseline_analysis_id=baseline.causal_analysis_id,
        study_id="synthetic_validation_study",
        intervention_id="synthetic_validation_intervention",
        treatment_provenance={"source": "synthetic deterministic fixture"},
        baseline_specification=baseline.causal_specification,
        variants=variants
        or (
            RobustnessVariant(
                variant_id="window_alt",
                variant_type=RobustnessVariantType.ALTERNATIVE_TIME_WINDOW,
                description="Reviewed alternative shorter window",
                methodological_rationale="Checks dependence on the pre/post window.",
                expected_diagnostic_purpose="time-window sensitivity",
                pre_treatment_window=(2018, 2019),
                post_treatment_window=(2020, 2021),
            ),
        ),
    )


def test_country_time_series_preserves_missing_years(causal_ingestion):
    spec = VisualizationSpecification(
        visualization_type=VisualizationType.COUNTRY_TIME_SERIES,
        source_artifact_id="synthetic_causal_panel",
        y_variable="outcome",
        entity_variable="entity",
        time_variable="year",
        selected_entities=("A", "B"),
        time_range=(2018, 2022),
    )

    artifact = build_visualization(specification=spec, source_artifact=causal_ingestion)

    assert artifact.visualization_id.startswith("viz_")
    assert len(artifact.plotting_data) == 10
    assert artifact.axis_metadata["y"].variable_id == "outcome"
    assert not any(row["missing"] for row in artifact.plotting_data)


def test_multi_country_trend_rejects_unreasonable_entity_count(causal_ingestion):
    with pytest.raises(ValueError, match="selected_entities exceeds"):
        VisualizationSpecification(
            visualization_type=VisualizationType.MULTI_COUNTRY_TREND,
            source_artifact_id="synthetic_causal_panel",
            y_variable="outcome",
            entity_variable="entity",
            time_variable="year",
            selected_entities=tuple(f"C{i}" for i in range(10)),
        )


def test_scatterplot_uses_analysis_sample(analysis_ingestion):
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
            ),
        )
    )
    spec = VisualizationSpecification(
        visualization_type=VisualizationType.SCATTERPLOT,
        source_artifact_id=analysis.result_id,
        x_variable="x",
        y_variable="y",
    )

    artifact = build_visualization(
        specification=spec,
        source_artifact=analysis,
        data_artifact=analysis_ingestion,
    )

    assert len(artifact.plotting_data) == analysis.analysis_sample.sample_size
    assert {row["source_sample"] for row in artifact.plotting_data} == {analysis.result_id}


def test_regression_relationship_reuses_existing_ols_coefficients(analysis_ingestion):
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
            ),
        )
    )
    artifact = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.REGRESSION_RELATIONSHIP,
            source_artifact_id=analysis.result_id,
            x_variable="x",
            y_variable="y",
        ),
        source_artifact=analysis,
        data_artifact=analysis_ingestion,
    )

    assert any(row.get("series") == "existing_ols_fitted_line" for row in artifact.plotting_data)
    assert any("existing Phase 4 coefficients" in item.text for item in artifact.annotations)


def test_ols_coefficient_plot_and_rendering(analysis_ingestion, tmp_path: Path):
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
                covariates=["z"],
            ),
        )
    )
    spec = VisualizationSpecification(
        visualization_type=VisualizationType.COEFFICIENT_PLOT,
        source_artifact_id=analysis.result_id,
        output_formats=(OutputFormat.PNG, OutputFormat.SVG, OutputFormat.CSV, OutputFormat.JSON),
    )

    artifact = build_visualization(specification=spec, source_artifact=analysis)
    exported = export_visualization(artifact, output_directory=tmp_path)

    assert [row["term"] for row in artifact.plotting_data] == ["x", "z"]
    assert (
        build_visualization(specification=spec, source_artifact=analysis).visualization_id
        == artifact.visualization_id
    )
    paths = {reference.format: Path(reference.path) for reference in exported.output_references}
    assert paths[OutputFormat.PNG].stat().st_size > 0
    assert paths[OutputFormat.SVG].stat().st_size > 0
    assert (
        paths[OutputFormat.CSV].read_text(encoding="utf-8").startswith("confidence_interval_high")
    )


def test_panel_coefficient_model_comparison_and_diagnostic(panel_ingestion):
    pooled = run_analysis(
        request=AnalysisRequest(
            ingestion_result=panel_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
                outcome="y",
            ),
        )
    )
    entity_fe = run_analysis(
        request=AnalysisRequest(
            ingestion_result=panel_ingestion,
            statistical_specification=panel_spec(procedure="panel_entity_fe"),
        )
    )
    twfe = run_analysis(
        request=AnalysisRequest(
            ingestion_result=panel_ingestion,
            statistical_specification=panel_spec(procedure="panel_two_way_fe"),
        )
    )

    comparison = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.MODEL_COMPARISON,
            source_artifact_id=pooled.result_id,
            selected_terms=("x",),
        ),
        source_artifact=pooled,
        comparison_artifacts=(entity_fe, twfe),
    )
    diagnostic = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.PANEL_DIAGNOSTIC,
            source_artifact_id=twfe.result_id,
            panel_diagnostic=PanelDiagnosticKind.WITHIN_BETWEEN_VARIATION,
        ),
        source_artifact=twfe,
    )

    assert [row["model_id"] for row in comparison.plotting_data] == [
        pooled.result_id,
        entity_fe.result_id,
        twfe.result_id,
    ]
    assert diagnostic.plotting_data
    assert "low_within_variation" in diagnostic.plotting_data[0]


def test_event_study_and_causal_estimate_preserve_semantics(tmp_path: Path):
    ingestion = synthetic_causal_ingestion(tmp_path)
    event_result = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=ingestion,
            causal_specification=causal_spec(event=True),
        )
    )

    event_artifact = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.EVENT_STUDY,
            source_artifact_id=event_result.causal_analysis_id,
        ),
        source_artifact=event_result,
    )
    estimate_artifact = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.CAUSAL_ESTIMATE,
            source_artifact_id=event_result.causal_analysis_id,
        ),
        source_artifact=event_result,
    )

    assert [row["event_time"] for row in event_artifact.plotting_data] == [-2, -1, 0, 1, 2]
    assert any(row["reference_period"] for row in event_artifact.plotting_data)
    assert estimate_artifact.plotting_data[0]["estimand"] == "att"
    assert any("Identifying assumptions" in item.text for item in estimate_artifact.annotations)


def test_robustness_leave_one_out_and_placebo_plots(tmp_path: Path):
    ingestion = synthetic_causal_ingestion(tmp_path)
    baseline = _baseline(ingestion)
    robustness = analyze_robustness(
        ingestion_result=ingestion,
        baseline_result=baseline,
        specification=_robustness_spec(
            baseline,
            variants=(
                RobustnessVariant(
                    variant_id="placebo_clean",
                    variant_type=RobustnessVariantType.PLACEBO_TIMING,
                    description="Reviewed placebo timing",
                    methodological_rationale="Checks pre-period timing.",
                    expected_diagnostic_purpose="placebo timing",
                    placebo_treatment_start_period=2019,
                    pre_treatment_window=(2018, 2018),
                    post_treatment_window=(2019, 2019),
                ),
                RobustnessVariant(
                    variant_id="too_many_rows_required",
                    variant_type=RobustnessVariantType.ALTERNATIVE_TIME_WINDOW,
                    description="Deliberately failed minimum sample check",
                    methodological_rationale="Validates failed variants remain visible.",
                    expected_diagnostic_purpose="failed variant retention",
                    pre_treatment_window=(2018, 2019),
                    post_treatment_window=(2020, 2022),
                    minimum_required_observations=10_000,
                ),
                RobustnessVariant(
                    variant_id="drop_treated_a",
                    variant_type=RobustnessVariantType.LEAVE_ONE_TREATED_ENTITY_OUT,
                    description="Leave A out",
                    methodological_rationale="Influence check.",
                    expected_diagnostic_purpose="leave-one-out",
                    omitted_entity="A",
                ),
            ),
        ),
    )

    estimates = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.ROBUSTNESS_ESTIMATES,
            source_artifact_id=robustness.robustness_analysis_id,
        ),
        source_artifact=robustness,
    )
    loo = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.LEAVE_ONE_OUT,
            source_artifact_id=robustness.robustness_analysis_id,
        ),
        source_artifact=robustness,
    )
    placebo = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.PLACEBO,
            source_artifact_id=robustness.robustness_analysis_id,
        ),
        source_artifact=robustness,
    )

    assert any(row.get("status") == "failed" for row in estimates.plotting_data)
    assert loo.plotting_data[0]["omitted_entity"] == "A"
    assert {row["series"] for row in placebo.plotting_data} == {"placebo", "actual"}


def test_correlation_missingness_coverage_and_distribution(analysis_ingestion):
    correlation = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="pearson_correlation",
                analysis_type="correlation",
                model_family="none",
                outcome="y",
                exposures=["x", "z"],
            ),
        )
    )
    matrix = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.CORRELATION_MATRIX,
            source_artifact_id=correlation.result_id,
            selected_variables=("x", "y", "z"),
        ),
        source_artifact=correlation,
    )
    missingness = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.MISSINGNESS_BY_VARIABLE,
            source_artifact_id="analysis_dataset",
            selected_variables=("x", "y", "z"),
        ),
        source_artifact=analysis_ingestion,
    )
    coverage = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.COUNTRY_YEAR_COVERAGE,
            source_artifact_id="analysis_dataset",
            entity_variable="category",
            time_variable="row_id",
            selected_variables=("x", "y"),
        ),
        source_artifact=analysis_ingestion,
    )
    distribution = build_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.DISTRIBUTION_HISTOGRAM,
            source_artifact_id="analysis_dataset",
            selected_variables=("x",),
        ),
        source_artifact=analysis_ingestion,
    )

    assert matrix.plotting_data
    assert any(
        row["variable"] == "y" and row["missing_count"] == 1 for row in missingness.plotting_data
    )
    assert any(not row["covered"] for row in coverage.plotting_data)
    assert len(distribution.plotting_data) == 9


def test_visual_integrity_rejects_unsupported_causal_title(causal_ingestion):
    spec = VisualizationSpecification(
        visualization_type=VisualizationType.COUNTRY_TIME_SERIES,
        source_artifact_id="synthetic_causal_panel",
        title="Treatment Improves Outcomes",
        y_variable="outcome",
        entity_variable="entity",
        time_variable="year",
        selected_entities=("A",),
    )
    with pytest.raises(VisualizationSpecificationError):
        build_visualization(specification=spec, source_artifact=causal_ingestion)


def test_mcp_create_list_and_get_visualization(causal_ingestion):
    service = MCPToolService()
    spec = VisualizationSpecification(
        visualization_type=VisualizationType.COUNTRY_TIME_SERIES,
        source_artifact_id="synthetic_causal_panel",
        y_variable="outcome",
        entity_variable="entity",
        time_variable="year",
        selected_entities=("A",),
    )

    response = service.call_tool(
        "create_visualization",
        {
            "visualization_specification": spec.model_dump(mode="json"),
            "source_artifact": causal_ingestion.model_dump(mode="json"),
        },
    )
    artifact = response["visualization"]["data"]
    listed = service.call_tool("list_visualizations", {"visualization_artifacts": [artifact]})
    fetched = service.call_tool(
        "get_visualization",
        {
            "visualization_id": artifact["visualization_id"],
            "visualization_artifacts": [artifact],
        },
    )

    assert response["artifact"]["artifact_type"] == "visualization_artifact"
    assert listed["visualizations"][0]["visualization_id"] == artifact["visualization_id"]
    assert fetched["visualization"]["data"]["visualization_id"] == artifact["visualization_id"]
