from __future__ import annotations

import pytest
from pydantic import ValidationError

from polaris.projects.models import ReasoningProjectConfig, ResearchStage
from polaris.projects.service import run_research_project
from polaris.reasoning import (
    CausalStatus,
    EpistemicStatus,
    ReasoningCategory,
    ReasoningMode,
    ReasoningRequest,
    ReasoningStatement,
    ReasoningStrictness,
    SupportLevel,
    build_reasoning_artifact,
)
from polaris.reasoning.errors import GroundingValidationError, ReasoningProviderError
from polaris.reasoning.models import StructuredReasoningResponse
from polaris.reasoning.validation import causal_language_violation, validate_reasoning_response
from polaris.synthesis.models import SynthesisRequest
from polaris.synthesis.service import synthesize_assessment
from tests.projects.helpers import single_manifest_project


class FakeReasoningProvider:
    provider_name = "fake-reasoning-provider"

    def __init__(self, response=None):
        self.response = response
        self.calls = 0
        self.payload = None

    def reason(self, *, request, system_prompt, grounding_payload):
        self.calls += 1
        self.payload = grounding_payload
        if self.response is not None:
            return self.response
        claim = request.evidence_artifact.claim_candidates[0]
        return StructuredReasoningResponse(
            reasoning_statements=(
                ReasoningStatement(
                    statement_id="provider_statement_1",
                    category=ReasoningCategory.EMPIRICAL_INTERPRETATION,
                    text=(
                        f"{claim.subject_variable} is associated with "
                        f"{claim.outcome_variable} in the supplied non-causal claim."
                    ),
                    evidence_ids=claim.supporting_evidence_ids,
                    claim_ids=(claim.claim_id,),
                    agent_assessment_ids=request.coordinated_assessment.source_assessment_ids,
                    domains=request.coordinated_assessment.participating_domains,
                    support_level=SupportLevel.LIMITED,
                    epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
                    causal_status=CausalStatus.NON_CAUSAL,
                ),
            )
        )


def completed_project(tmp_path, *, reasoning=None, provider=None):
    request = single_manifest_project(tmp_path)
    if reasoning is not None:
        request = request.model_copy(update={"reasoning": reasoning})
    return run_research_project(request, reasoning_provider=provider)


def reasoning_request_from_result(result, *, mode=ReasoningMode.DETERMINISTIC, strictness=None):
    return ReasoningRequest(
        research_question=result.request.research_question.raw_text,
        evidence_artifact=result.evidence_artifact,
        coordinated_assessment=result.coordinated_assessment,
        mode=mode,
        strictness=strictness or ReasoningStrictness(),
    )


def test_reasoning_disabled_preserves_phase13_path(tmp_path):
    result = completed_project(tmp_path)

    assert ResearchStage.REASON not in result.execution_plan.stages
    assert result.reasoning_artifact is None
    assert result.research_report.report.evidence_grounded_interpretation_section is None


def test_deterministic_reasoning_project_stage_and_report(tmp_path):
    result = completed_project(
        tmp_path,
        reasoning=ReasoningProjectConfig(enabled=True, mode=ReasoningMode.DETERMINISTIC),
    )

    assert ResearchStage.REASON in result.execution_plan.stages
    assert result.reasoning_artifact is not None
    assert result.synthesis_artifact.referenced_reasoning_statement_ids
    section = result.research_report.report.evidence_grounded_interpretation_section
    assert section is not None
    assert section.main_interpretations
    assert "Evidence-Grounded Interpretation" in result.research_report.rendered_content


def test_models_are_strict_frozen_and_deterministic(tmp_path):
    result = completed_project(tmp_path)
    request = reasoning_request_from_result(result)
    artifact_a = build_reasoning_artifact(request=request)
    artifact_b = build_reasoning_artifact(request=request)

    assert artifact_a.reasoning_id == artifact_b.reasoning_id
    assert artifact_a.model_dump_json() != ""
    with pytest.raises(ValidationError):
        ReasoningRequest.model_validate(
            {
                **request.model_dump(mode="json"),
                "unknown": "rejected",
            }
        )
    with pytest.raises(ValidationError):
        artifact_a.reasoning_statements[0].text = "mutated"


def test_taxonomy_categories_are_supported():
    expected = {
        "empirical_interpretation",
        "cross_domain_synthesis",
        "plausible_mechanism",
        "alternative_explanation",
        "potential_confounder",
        "contradiction",
        "limitation",
        "uncertainty",
        "follow_up_hypothesis",
        "follow_up_research_question",
        "literature_alignment",
        "literature_contrast",
    }
    assert {category.value for category in ReasoningCategory} == expected


def test_grounding_rejects_unknown_ids(tmp_path):
    result = completed_project(tmp_path)
    request = reasoning_request_from_result(result)
    claim = result.evidence_artifact.claim_candidates[0]
    statement = ReasoningStatement(
        statement_id="bad_grounding",
        category=ReasoningCategory.EMPIRICAL_INTERPRETATION,
        text="x is associated with y in the supplied non-causal claim.",
        evidence_ids=("unknown_evidence",),
        claim_ids=(claim.claim_id,),
        agent_assessment_ids=result.coordinated_assessment.source_assessment_ids,
        domains=result.coordinated_assessment.participating_domains,
        support_level=SupportLevel.LIMITED,
        epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
    )

    with pytest.raises(GroundingValidationError):
        validate_reasoning_response(
            StructuredReasoningResponse(reasoning_statements=(statement,)),
            request,
        )


def test_mechanism_guardrails():
    with pytest.raises(ValidationError):
        ReasoningStatement(
            statement_id="mechanism_as_fact",
            category=ReasoningCategory.PLAUSIBLE_MECHANISM,
            text="x is a mechanism for y.",
            evidence_ids=("evidence_1",),
            support_level=SupportLevel.LIMITED,
            epistemic_status=EpistemicStatus.DIRECTLY_SUPPORTED,
            causal_status=CausalStatus.NON_CAUSAL,
        )

    valid = ReasoningStatement(
        statement_id="mechanism_valid",
        category=ReasoningCategory.PLAUSIBLE_MECHANISM,
        text="x may plausibly contribute to y, but causality is not established.",
        evidence_ids=("evidence_1",),
        support_level=SupportLevel.LIMITED,
        epistemic_status=EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN,
        causal_status=CausalStatus.NOT_ESTABLISHED,
        limitations=("mechanism not directly tested",),
    )
    assert causal_language_violation(valid) is None


@pytest.mark.parametrize(
    "text",
    ("X causes Y.", "X drives Y.", "X improves Y.", "the impact of X on Y"),
)
def test_causal_guard_blocks_unsupported_language(text):
    statement = ReasoningStatement(
        statement_id="causal_bad",
        category=ReasoningCategory.EMPIRICAL_INTERPRETATION,
        text=text,
        evidence_ids=("evidence_1",),
        support_level=SupportLevel.LIMITED,
        epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
    )
    assert causal_language_violation(statement) is not None


@pytest.mark.parametrize(
    "text",
    (
        "X is associated with Y.",
        "The causal effect cannot be inferred from this evidence.",
    ),
)
def test_causal_guard_allows_noncausal_language(text):
    statement = ReasoningStatement(
        statement_id="causal_allowed",
        category=ReasoningCategory.EMPIRICAL_INTERPRETATION,
        text=text,
        evidence_ids=("evidence_1",),
        support_level=SupportLevel.LIMITED,
        epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
    )
    assert causal_language_violation(statement) is None


def test_provider_backed_reasoning_uses_structured_payload(tmp_path):
    result = completed_project(tmp_path)
    provider = FakeReasoningProvider()
    request = reasoning_request_from_result(result, mode=ReasoningMode.PROVIDER_BACKED)
    artifact = build_reasoning_artifact(request=request, provider=provider)

    assert provider.calls == 1
    assert provider.payload["evidence_records"]
    assert artifact.mode is ReasoningMode.PROVIDER_BACKED
    assert artifact.reasoning_statements[0].claim_ids


def test_provider_malformed_output_falls_back(tmp_path):
    result = completed_project(tmp_path)
    provider = FakeReasoningProvider(response={"reasoning_statements": []})
    request = reasoning_request_from_result(result, mode=ReasoningMode.PROVIDER_BACKED)

    artifact = build_reasoning_artifact(request=request, provider=provider)

    assert artifact.deterministic_fallback_used is True
    assert artifact.mode is ReasoningMode.DETERMINISTIC


def test_provider_causal_violation_rejected_when_fallback_disabled(tmp_path):
    result = completed_project(tmp_path)
    claim = result.evidence_artifact.claim_candidates[0]
    bad_response = StructuredReasoningResponse(
        reasoning_statements=(
            ReasoningStatement(
                statement_id="provider_bad_causal",
                category=ReasoningCategory.EMPIRICAL_INTERPRETATION,
                text="x causes y.",
                evidence_ids=claim.supporting_evidence_ids,
                claim_ids=(claim.claim_id,),
                agent_assessment_ids=result.coordinated_assessment.source_assessment_ids,
                domains=result.coordinated_assessment.participating_domains,
                support_level=SupportLevel.LIMITED,
                epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
            ),
        )
    )
    request = reasoning_request_from_result(
        result,
        mode=ReasoningMode.PROVIDER_BACKED,
        strictness=ReasoningStrictness(allow_provider_fallback=False),
    )

    with pytest.raises(ReasoningProviderError):
        build_reasoning_artifact(request=request, provider=FakeReasoningProvider(bad_response))


def test_phase8_synthesis_with_and_without_reasoning(tmp_path):
    result = completed_project(tmp_path)
    base = synthesize_assessment(
        request=SynthesisRequest(
            coordinated_assessment=result.coordinated_assessment,
            evidence_artifact=result.evidence_artifact,
        )
    )
    reasoning = build_reasoning_artifact(request=reasoning_request_from_result(result))
    with_reasoning = synthesize_assessment(
        request=SynthesisRequest(
            coordinated_assessment=result.coordinated_assessment,
            evidence_artifact=result.evidence_artifact,
            reasoning_artifact=reasoning,
        )
    )

    assert base.referenced_reasoning_statement_ids == ()
    assert with_reasoning.referenced_reasoning_statement_ids
    assert base.referenced_claim_ids == with_reasoning.referenced_claim_ids
