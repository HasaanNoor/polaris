import pytest

from polaris.agents.models import AgentDomain
from polaris.agents.service import run_domain_agent
from polaris.analysis.causal import CausalAnalysisRequest, run_causal_analysis
from polaris.analysis.causal.errors import (
    InsufficientPreTreatmentDataError,
    MissingControlGroupError,
    UnsupportedStaggeredTreatmentError,
)
from polaris.coordination.service import coordinate_assessments
from polaris.evidence.models import ClaimType, EvidenceType
from polaris.evidence.service import extract_evidence
from polaris.mcp.tools import MCPToolService
from polaris.projects.models import IngestionArtifactInput
from polaris.projects.service import run_research_project
from polaris.reasoning.models import ReasoningRequest
from polaris.reasoning.service import build_reasoning_artifact
from polaris.reasoning.taxonomy import CausalStatus, ReasoningMode
from tests.analysis.causal.conftest import (
    causal_spec,
    statistical_spec,
    synthetic_causal_ingestion,
)
from tests.projects.helpers import base_request


def test_simple_did_and_twfe_recover_known_positive_att(causal_ingestion):
    result = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=causal_ingestion,
            causal_specification=causal_spec(),
        )
    )

    assert result.treatment_effect.estimate == pytest.approx(3.0, abs=1e-8)
    assert result.treatment_effect.component_means is not None
    assert result.sample_summary.treated_entity_count == 3
    assert result.sample_summary.control_entity_count == 3
    assert result.assumptions
    assert result.diagnostics.parallel_trends.status in {
        "insufficient_pre_treatment_data",
        "no_obvious_pre_treatment_divergence_detected",
    }


def test_zero_effect_case_works(tmp_path):
    ingestion = synthetic_causal_ingestion(tmp_path, effect=0.0)
    result = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=ingestion, causal_specification=causal_spec()
        )
    )

    assert result.treatment_effect.estimate == pytest.approx(0.0, abs=1e-8)


def test_event_study_reference_period_and_plot_data(causal_ingestion):
    result = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=causal_ingestion,
            causal_specification=causal_spec(event=True),
        )
    )

    reference = [item for item in result.event_study_results if item.reference_period]
    assert len(reference) == 1
    assert reference[0].event_time == -1
    assert reference[0].coefficient is None
    assert result.sample_summary.event_window_excluded_rows == 0


def test_parallel_trend_concern_is_reported(tmp_path):
    ingestion = synthetic_causal_ingestion(tmp_path, pretrend=True)
    result = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=ingestion,
            causal_specification=causal_spec(event=True),
        )
    )

    assert "pre_treatment" in result.diagnostics.parallel_trends.status.value
    assert any(assumption.assumption_code == "parallel_trends" for assumption in result.assumptions)


def test_missing_pre_period_and_no_controls_rejected(tmp_path):
    missing_pre = synthetic_causal_ingestion(tmp_path, missing_pre_entity="A")
    with pytest.raises(InsufficientPreTreatmentDataError):
        run_causal_analysis(
            request=CausalAnalysisRequest(
                ingestion_result=missing_pre,
                causal_specification=causal_spec(),
            )
        )

    no_controls = synthetic_causal_ingestion(tmp_path, no_controls=True)
    with pytest.raises(MissingControlGroupError):
        run_causal_analysis(
            request=CausalAnalysisRequest(
                ingestion_result=no_controls,
                causal_specification=causal_spec(),
            )
        )


def test_staggered_adoption_rejected(tmp_path):
    ingestion = synthetic_causal_ingestion(tmp_path, staggered=True)
    with pytest.raises(UnsupportedStaggeredTreatmentError):
        run_causal_analysis(
            request=CausalAnalysisRequest(
                ingestion_result=ingestion, causal_specification=causal_spec()
            )
        )


def test_post_treatment_control_warning(causal_ingestion):
    result = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=causal_ingestion,
            causal_specification=causal_spec(covariates=("post_control",)),
        )
    )

    assert any("post-treatment" in limitation for limitation in result.limitations)
    assert any(finding.method == "causal_design" for finding in result.findings)


def test_phase5_causal_evidence_and_conditional_reasoning(causal_ingestion):
    causal = run_causal_analysis(
        request=CausalAnalysisRequest(
            ingestion_result=causal_ingestion,
            causal_specification=causal_spec(),
        )
    )
    evidence = extract_evidence(analysis_result=causal)

    assert any(
        record.evidence_type is EvidenceType.CAUSAL_TREATMENT_EFFECT
        for record in evidence.evidence_records
    )
    causal_claims = [
        claim
        for claim in evidence.claim_candidates
        if claim.claim_type is ClaimType.CAUSAL_DESIGN_ESTIMATE
    ]
    assert causal_claims
    assert all(claim.causal for claim in causal_claims)

    coordinated = coordinate_assessments(
        assessments=(
            run_domain_agent(domain=AgentDomain.ECONOMICS, evidence_artifact=evidence),
            run_domain_agent(domain=AgentDomain.GOVERNANCE, evidence_artifact=evidence),
        )
    )
    reasoning = build_reasoning_artifact(
        request=ReasoningRequest(
            research_question="What is the treatment effect in the synthetic DiD design?",
            evidence_artifact=evidence,
            coordinated_assessment=coordinated,
            mode=ReasoningMode.DETERMINISTIC,
        )
    )
    text = " ".join(statement.text for statement in reasoning.reasoning_statements)
    assert "Under the difference-in-differences design" in text
    assert any(
        statement.causal_status is CausalStatus.CONDITIONAL_CAUSAL_DESIGN
        for statement in reasoning.reasoning_statements
    )


def test_phase13_project_and_mcp_require_explicit_causal_config(causal_ingestion):
    project = base_request(
        dataset_inputs=(IngestionArtifactInput(ingestion_result=causal_ingestion),),
        statistical_specification=statistical_spec(),
    ).model_copy(update={"causal_specification": causal_spec()})
    result = run_research_project(project)
    assert result.causal_analysis_result is not None
    assert any(claim.causal for claim in result.evidence_artifact.claim_candidates)

    service = MCPToolService()
    valid = service.call_tool(
        "run_causal_analysis",
        {
            "ingestion_result": causal_ingestion.model_dump(mode="json"),
            "causal_specification": causal_spec().model_dump(mode="json"),
        },
    )
    invalid = service.call_tool(
        "run_causal_analysis",
        {
            "ingestion_result": causal_ingestion.model_dump(mode="json"),
            "causal_specification": {"method": "difference_in_differences"},
        },
    )
    assert valid["artifact"]["artifact_type"] == "causal_analysis_result"
    assert "error" in invalid
