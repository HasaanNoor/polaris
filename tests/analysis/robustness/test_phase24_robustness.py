from pathlib import Path

import pytest

from polaris.agents.models import AgentDomain
from polaris.agents.service import run_domain_agent
from polaris.analysis.causal import CausalAnalysisRequest, run_causal_analysis
from polaris.analysis.robustness import (
    RobustnessSpecification,
    RobustnessVariant,
    RobustnessVariantType,
    analyze_robustness,
)
from polaris.analysis.robustness.models import RobustnessEvidenceStatus
from polaris.analysis.robustness.service import assess_real_study_execution_readiness
from polaris.coordination.service import coordinate_assessments
from polaris.evidence.models import EvidenceType
from polaris.evidence.service import extract_evidence
from polaris.mcp.tools import MCPToolService
from polaris.projects.models import IngestionArtifactInput, ResearchStage, RobustnessProjectConfig
from polaris.projects.service import run_research_project
from polaris.reasoning.models import ReasoningRequest
from polaris.reasoning.service import build_reasoning_artifact
from polaris.reasoning.taxonomy import ReasoningMode
from tests.analysis.causal.conftest import (
    causal_spec,
    statistical_spec,
    synthetic_causal_ingestion,
)
from tests.projects.helpers import base_request


def test_stable_effect_across_explicit_specifications(tmp_path: Path):
    causal_ingestion = synthetic_causal_ingestion(tmp_path)
    baseline = _baseline(causal_ingestion)
    result = analyze_robustness(
        ingestion_result=causal_ingestion,
        baseline_result=baseline,
        specification=_robustness_spec(baseline),
        significance_threshold=0.05,
    )

    assert result.treatment_effect_stability.baseline_estimate == pytest.approx(3.0)
    assert result.treatment_effect_stability.successful_variant_count >= 4
    assert result.robustness_evidence_status in {
        RobustnessEvidenceStatus.ROBUSTNESS_CONSISTENT,
        RobustnessEvidenceStatus.ROBUSTNESS_MIXED,
    }
    assert "robustness_estimates.csv" in result.plotting_artifacts
    assert result.failed_variants
    assert not hasattr(result, "robustness_score")


def test_control_group_and_time_window_sensitivity(tmp_path: Path):
    ingestion = synthetic_causal_ingestion(tmp_path, effect=3.0, pretrend=True)
    baseline = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=ingestion,
            causal_specification=causal_spec(extra={"post_treatment_window": (2020, 2021)}),
        )
    )
    result = analyze_robustness(
        ingestion_result=ingestion,
        baseline_result=baseline,
        specification=_robustness_spec(
            baseline,
            variants=(
                RobustnessVariant(
                    variant_id="window_sensitive",
                    variant_type=RobustnessVariantType.ALTERNATIVE_TIME_WINDOW,
                    description="Shorter reviewed post window",
                    methodological_rationale="Checks whether early post years drive estimates.",
                    expected_diagnostic_purpose="time-window sensitivity",
                    pre_treatment_window=(2019, 2019),
                    post_treatment_window=(2020, 2020),
                ),
                RobustnessVariant(
                    variant_id="controls_subset",
                    variant_type=RobustnessVariantType.ALTERNATIVE_CONTROL_GROUP,
                    description="Explicit subset of controls",
                    methodological_rationale="Checks dependence on reviewed control set.",
                    expected_diagnostic_purpose="control-group sensitivity",
                    control_entities=("D",),
                ),
            ),
        ),
    )

    assert {item.variant_type for item in result.variant_results} == {
        RobustnessVariantType.ALTERNATIVE_TIME_WINDOW,
        RobustnessVariantType.ALTERNATIVE_CONTROL_GROUP,
    }
    assert any(
        item.observation_changes.included_row_numbers_removed for item in result.variant_results
    )


def test_leave_one_out_and_placebo_diagnostics(tmp_path: Path):
    causal_ingestion = synthetic_causal_ingestion(tmp_path)
    baseline = _baseline(causal_ingestion)
    result = analyze_robustness(
        ingestion_result=causal_ingestion,
        baseline_result=baseline,
        specification=_robustness_spec(
            baseline,
            variants=(
                _loo("drop_treated_a", RobustnessVariantType.LEAVE_ONE_TREATED_ENTITY_OUT, "A"),
                _loo("drop_control_d", RobustnessVariantType.LEAVE_ONE_CONTROL_ENTITY_OUT, "D"),
                RobustnessVariant(
                    variant_id="placebo_clean",
                    variant_type=RobustnessVariantType.PLACEBO_TIMING,
                    description="Reviewed placebo timing in the pre-period",
                    methodological_rationale="Checks for effects before treatment starts.",
                    expected_diagnostic_purpose="placebo timing",
                    placebo_treatment_start_period=2019,
                    pre_treatment_window=(2018, 2018),
                    post_treatment_window=(2019, 2019),
                ),
                RobustnessVariant(
                    variant_id="placebo_assignment",
                    variant_type=RobustnessVariantType.PLACEBO_ASSIGNMENT,
                    description="Explicit placebo assignment to a known control",
                    methodological_rationale="Falsification using predefined control entity.",
                    expected_diagnostic_purpose="placebo assignment",
                    placebo_treated_entities=("D",),
                ),
            ),
        ),
    )

    assert {item.omitted_role for item in result.leave_one_out_results} == {"treated", "control"}
    assert len(result.placebo_results) == 2
    assert all("proof" not in item.diagnostic_interpretation for item in result.placebo_results)


def test_event_window_sensitivity_preserves_event_time(tmp_path: Path):
    causal_ingestion = synthetic_causal_ingestion(tmp_path)
    baseline = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=causal_ingestion,
            causal_specification=causal_spec(event=True),
        )
    )
    result = analyze_robustness(
        ingestion_result=causal_ingestion,
        baseline_result=baseline,
        specification=_robustness_spec(
            baseline,
            variants=(
                RobustnessVariant(
                    variant_id="event_window_short",
                    variant_type=RobustnessVariantType.EVENT_STUDY_WINDOW,
                    description="Shorter event-study window",
                    methodological_rationale="Checks dependence on event-window endpoints.",
                    expected_diagnostic_purpose="event-study sensitivity",
                    event_study_window=(-1, 1),
                    event_study_reference_period=-1,
                ),
            ),
        ),
    )

    assert result.event_study_comparison
    assert {item.omitted_reference_period for item in result.event_study_comparison} == {-1}


def test_evidence_reasoning_project_and_mcp_integration(tmp_path: Path):
    causal_ingestion = synthetic_causal_ingestion(tmp_path)
    baseline = _baseline(causal_ingestion)
    spec = _robustness_spec(baseline)
    robustness = analyze_robustness(
        ingestion_result=causal_ingestion,
        baseline_result=baseline,
        specification=spec,
        significance_threshold=0.05,
    )
    evidence = extract_evidence(analysis_result=baseline, robustness_result=robustness)
    assert any(
        record.evidence_type is EvidenceType.CAUSAL_ROBUSTNESS
        for record in evidence.evidence_records
    )

    coordinated = coordinate_assessments(
        assessments=(run_domain_agent(domain=AgentDomain.ECONOMICS, evidence_artifact=evidence),)
    )
    reasoning = build_reasoning_artifact(
        request=ReasoningRequest(
            research_question="What does robustness imply?",
            evidence_artifact=evidence,
            coordinated_assessment=coordinated,
            mode=ReasoningMode.DETERMINISTIC,
        )
    )
    assert "does not resolve the identifying assumptions" in " ".join(
        item.text for item in reasoning.reasoning_statements
    )

    project = base_request(
        dataset_inputs=(IngestionArtifactInput(ingestion_result=causal_ingestion),),
        statistical_specification=statistical_spec(),
    ).model_copy(
        update={
            "causal_specification": baseline.causal_specification,
            "robustness": RobustnessProjectConfig(enabled=True, specification=spec),
        }
    )
    project_result = run_research_project(project)
    assert ResearchStage.ROBUSTNESS in project_result.execution_plan.stages
    assert project_result.robustness_result is not None
    assert project_result.research_report.report.robustness_section is not None

    service = MCPToolService()
    response = service.call_tool(
        "run_robustness_analysis",
        {
            "ingestion_result": causal_ingestion.model_dump(mode="json"),
            "baseline_result": baseline.model_dump(mode="json"),
            "robustness_specification": spec.model_dump(mode="json"),
            "significance_threshold": 0.05,
        },
    )
    assert response["artifact"]["artifact_type"] == "robustness_analysis_result"


def test_current_phase23_registry_blocks_real_execution():
    blocks = assess_real_study_execution_readiness()

    assert blocks
    assert all(block.review_status != "design_ready" for block in blocks)
    assert all(block.blocking_reasons for block in blocks)


def _baseline(ingestion):
    return run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=ingestion,
            causal_specification=causal_spec(),
        )
    )


def _robustness_spec(baseline, variants=None):
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
            RobustnessVariant(
                variant_id="controls_de",
                variant_type=RobustnessVariantType.ALTERNATIVE_CONTROL_GROUP,
                description="Explicit alternative control set",
                methodological_rationale="Uses a predefined subset of reviewed controls.",
                expected_diagnostic_purpose="control-group sensitivity",
                control_entities=("D", "E"),
            ),
            RobustnessVariant(
                variant_id="covariate_empty",
                variant_type=RobustnessVariantType.COVARIATE_SET,
                description="No covariates",
                methodological_rationale="Checks baseline no-covariate design.",
                expected_diagnostic_purpose="covariate sensitivity",
                covariates=(),
            ),
            _loo("drop_treated_a", RobustnessVariantType.LEAVE_ONE_TREATED_ENTITY_OUT, "A"),
            _loo("drop_control_d", RobustnessVariantType.LEAVE_ONE_CONTROL_ENTITY_OUT, "D"),
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
        ),
    )


def _loo(variant_id, variant_type, entity):
    return RobustnessVariant(
        variant_id=variant_id,
        variant_type=variant_type,
        description=f"Leave {entity} out",
        methodological_rationale="Checks whether one entity dominates the estimate.",
        expected_diagnostic_purpose="leave-one-out sensitivity",
        omitted_entity=entity,
    )
