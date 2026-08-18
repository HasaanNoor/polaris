import pytest

from polaris.analysis.errors import (
    DuplicatePanelKeyError,
    PanelSpecificationError,
    TimeInvariantPredictorError,
)
from polaris.analysis.models import AnalysisRequest, PanelRegressionResult
from polaris.analysis.service import run_analysis
from polaris.evaluation.causality import evaluate_causal_restraint
from polaris.evidence.service import extract_evidence
from polaris.mcp.tools import MCPToolService
from polaris.projects.models import IngestionArtifactInput, ReasoningProjectConfig, ResearchStage
from polaris.projects.service import run_research_project
from polaris.reasoning.models import ReasoningRequest, ReasoningStatement
from polaris.reasoning.service import build_reasoning_artifact
from polaris.reasoning.taxonomy import (
    EpistemicStatus,
    ReasoningCategory,
    ReasoningMode,
    SupportLevel,
)
from polaris.schemas.statistics import StatisticalSpecification
from tests.projects.helpers import base_request

from .conftest import panel_spec


def test_two_way_fixed_effects_recovers_known_coefficient(panel_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=panel_ingestion,
            statistical_specification=panel_spec(covariates=["z"]),
            significance_threshold=0.05,
        )
    )

    model = result.method_result
    assert isinstance(model, PanelRegressionResult)
    assert result.analysis_method == "panel_two_way_fe"
    assert model.fixed_effects.entity_fixed_effects is True
    assert model.fixed_effects.time_fixed_effects is True
    assert model.fixed_effects.intercept_reported is False
    assert model.panel_sample.entity_count == 4
    assert model.panel_sample.time_period_count == 4
    assert model.panel_sample.balanced is True
    assert model.cluster.strategy == "cluster_robust_entity"
    assert model.cluster.cluster_count == 4
    assert model.coefficients[0].term == "x"
    assert model.coefficients[0].estimate == pytest.approx(2.0, abs=0.08)
    assert model.coefficients[0].standard_error_type == "cluster_robust_entity"
    assert model.fit.within_r_squared is not None
    assert model.transformed_condition_number is not None
    assert any(finding.code == "low_cluster_count" for finding in model.warnings)


def test_entity_fixed_effects_uses_within_entity_variation(panel_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=panel_ingestion,
            statistical_specification=panel_spec(procedure="panel_entity_fe", covariates=["z"]),
        )
    )

    model = result.method_result
    assert isinstance(model, PanelRegressionResult)
    assert model.fixed_effects.entity_fixed_effects is True
    assert model.fixed_effects.time_fixed_effects is False
    assert model.panel_sample.effective_model_sample == 16


def test_panel_rejects_time_invariant_predictor(panel_ingestion):
    with pytest.raises(TimeInvariantPredictorError):
        run_analysis(
            request=AnalysisRequest(
                ingestion_result=panel_ingestion,
                statistical_specification=panel_spec(exposures=["time_invariant"]),
            )
        )


def test_panel_requires_entity_and_entity_clustering(panel_ingestion):
    missing_entity = panel_spec(extra={"entity_variable": None})
    with pytest.raises(PanelSpecificationError):
        run_analysis(
            request=AnalysisRequest(
                ingestion_result=panel_ingestion,
                statistical_specification=missing_entity,
            )
        )

    invalid_cluster = panel_spec(
        extra={
            "standard_error_strategy": {
                "strategy": "cluster_robust",
                "cluster_variables": [{"variable_id": "year"}],
            }
        }
    )
    with pytest.raises(PanelSpecificationError):
        run_analysis(
            request=AnalysisRequest(
                ingestion_result=panel_ingestion,
                statistical_specification=invalid_cluster,
            )
        )


def test_lag_generation_stays_within_entity(panel_ingestion):
    spec = panel_spec(
        exposures=[],
        covariates=[],
        extra={
            "exposure_variables": [],
            "lags": [
                {
                    "source_variable": {"variable_id": "x"},
                    "lag_periods": 1,
                    "generated_variable_id": "x_lag1",
                }
            ],
        },
    )
    result = run_analysis(
        request=AnalysisRequest(ingestion_result=panel_ingestion, statistical_specification=spec)
    )

    model = result.method_result
    assert isinstance(model, PanelRegressionResult)
    assert model.predictor_variable_ids == ("x_lag1",)
    assert model.lag_operations[0].rows_lost == 4
    assert model.panel_sample.included_rows == 12
    first_included = result.provenance.included_row_numbers[0]
    assert first_included != 1


def test_lag_generation_rejects_year_gaps(panel_ingestion):
    gapped = panel_ingestion.model_copy(
        update={
            "normalized_records": tuple(
                record for record in panel_ingestion.normalized_records if record.row_number != 2
            )
        }
    )
    spec = panel_spec(
        exposures=[],
        covariates=[],
        extra={
            "exposure_variables": [],
            "lags": [
                {
                    "source_variable": {"variable_id": "x"},
                    "lag_periods": 1,
                    "generated_variable_id": "x_lag1",
                }
            ],
        },
    )
    result = run_analysis(
        request=AnalysisRequest(ingestion_result=gapped, statistical_specification=spec)
    )

    model = result.method_result
    assert isinstance(model, PanelRegressionResult)
    assert model.lag_operations[0].rows_lost == 5
    assert (3, "missing required consecutive prior period") in model.lag_operations[
        0
    ].missing_lag_reasons


def test_first_difference_requires_and_uses_consecutive_changes(panel_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=panel_ingestion,
            statistical_specification=panel_spec(procedure="first_difference", covariates=["z"]),
        )
    )

    model = result.method_result
    assert isinstance(model, PanelRegressionResult)
    assert model.procedure == "first_difference"
    assert model.fixed_effects.entity_fixed_effects is False
    assert model.panel_sample.included_rows == 12
    assert model.coefficients[0].estimate > 0
    assert model.coefficients[0].standard_error_type == "cluster_robust_entity"


def test_panel_evidence_extraction_is_compatible(panel_ingestion):
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=panel_ingestion,
            statistical_specification=panel_spec(covariates=["z"]),
        )
    )
    evidence = extract_evidence(analysis_result=analysis)

    assert any(
        record.evidence_type == "regression_coefficient" for record in evidence.evidence_records
    )
    assert any(record.evidence_type == "model_fit" for record in evidence.evidence_records)
    assert any(
        record.statistical_procedure == "panel_two_way_fe" for record in evidence.evidence_records
    )
    assert all(not claim.causal for claim in evidence.claim_candidates)


def test_phase13_project_and_phase18_reasoning_accept_panel_spec(panel_ingestion, tmp_path):
    request = base_request(
        dataset_inputs=(IngestionArtifactInput(ingestion_result=panel_ingestion),),
        statistical_specification=panel_spec(covariates=["z"]),
        output_directory=tmp_path / "outputs",
    ).model_copy(
        update={"reasoning": ReasoningProjectConfig(enabled=True, mode=ReasoningMode.DETERMINISTIC)}
    )
    result = run_research_project(request)

    assert result.overall_status == "completed"
    assert result.analysis_result.analysis_method == "panel_two_way_fe"
    assert ResearchStage.REASON in result.execution_plan.stages
    text = " ".join(statement.text for statement in result.reasoning_artifact.reasoning_statements)
    assert "within-entity longitudinal variation" in text
    assert "non-causal" in text


def test_phase19_causal_restraint_flags_panel_overclaim(panel_ingestion):
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=panel_ingestion,
            statistical_specification=panel_spec(covariates=["z"]),
        )
    )
    evidence = extract_evidence(analysis_result=analysis)
    project = base_request(
        dataset_inputs=(IngestionArtifactInput(ingestion_result=panel_ingestion),),
        statistical_specification=panel_spec(covariates=["z"]),
    )
    project_result = run_research_project(project)
    reasoning = build_reasoning_artifact(
        request=ReasoningRequest(
            research_question=project.research_question.raw_text,
            evidence_artifact=evidence,
            coordinated_assessment=project_result.coordinated_assessment,
            mode=ReasoningMode.DETERMINISTIC,
        )
    )
    flawed = reasoning.model_copy(
        update={
            "reasoning_statements": (
                ReasoningStatement(
                    statement_id="panel_causal_overclaim",
                    category=ReasoningCategory.EMPIRICAL_INTERPRETATION,
                    text="Fixed effects prove that changes in x caused changes in y.",
                    evidence_ids=reasoning.reasoning_statements[0].evidence_ids,
                    claim_ids=reasoning.reasoning_statements[0].claim_ids,
                    support_level=SupportLevel.LIMITED,
                    epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
                ),
                *reasoning.reasoning_statements[1:],
            )
        }
    )

    assert evaluate_causal_restraint(reasoning).passed is True
    assert evaluate_causal_restraint(flawed).passed is False


def test_phase20_mcp_accepts_panel_specification(panel_ingestion):
    service = MCPToolService()
    valid = service.call_tool(
        "run_analysis",
        {
            "ingestion_result": panel_ingestion.model_dump(mode="json"),
            "statistical_specification": panel_spec(covariates=["z"]).model_dump(mode="json"),
        },
    )
    invalid_spec = panel_spec(covariates=["z"]).model_dump(mode="json")
    invalid_spec["entity_variable"] = None
    invalid = service.call_tool(
        "run_analysis",
        {
            "ingestion_result": panel_ingestion.model_dump(mode="json"),
            "statistical_specification": invalid_spec,
        },
    )

    assert valid["artifact"]["artifact_type"] == "analysis_result"
    assert valid["artifact"]["summary"]["analysis_method"] == "panel_two_way_fe"
    assert invalid["error"]["category"] in {"validation", "execution"}


def test_duplicate_entity_time_key_rejected(tmp_path, panel_ingestion):
    path = tmp_path / "duplicate.csv"
    source = panel_ingestion.ingestion_request.source_path.read_text(encoding="utf-8")
    path.write_text(source + "A,2020,1,1,1,1,A\n", encoding="utf-8")
    ingestion = panel_ingestion.model_copy(
        update={
            "ingestion_request": panel_ingestion.ingestion_request.model_copy(
                update={"source_path": path}
            ),
            "normalized_records": (
                *panel_ingestion.normalized_records,
                panel_ingestion.normalized_records[0].model_copy(
                    update={"row_number": 17, "source_line_number": 18}
                ),
            ),
        }
    )

    with pytest.raises(DuplicatePanelKeyError):
        run_analysis(
            request=AnalysisRequest(
                ingestion_result=ingestion,
                statistical_specification=panel_spec(covariates=["z"]),
            )
        )


def test_panel_specification_json_round_trip():
    spec = panel_spec(
        extra={
            "lags": [{"source_variable": {"variable_id": "x"}, "lag_periods": 1}],
        }
    )
    restored = StatisticalSpecification.model_validate_json(spec.model_dump_json())

    assert restored.procedure == "panel_two_way_fe"
    assert restored.entity_variable.variable_id == "entity"
    assert restored.lags[0].source_variable.variable_id == "x"
