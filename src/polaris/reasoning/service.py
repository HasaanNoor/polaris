"""Public API for Phase 18 evidence-grounded reasoning."""

from datetime import UTC, datetime

from polaris.evidence.provenance import deterministic_id
from polaris.reasoning.deterministic import deterministic_reasoning_artifact
from polaris.reasoning.errors import (
    GroundingValidationError,
    ReasoningProviderError,
    ReasoningValidationError,
    UnsupportedReasoningModeError,
)
from polaris.reasoning.models import (
    REASONING_RULESET_VERSION,
    REASONING_SCHEMA_VERSION,
    GroundingSummary,
    ReasoningArtifact,
    ReasoningProvenance,
    ReasoningRequest,
    StructuredReasoningResponse,
)
from polaris.reasoning.prompts import build_prompt_inputs
from polaris.reasoning.provider import ReasoningProvider
from polaris.reasoning.taxonomy import EpistemicStatus, ReasoningCategory, ReasoningMode
from polaris.reasoning.validation import parse_provider_response, validate_reasoning_response


def build_reasoning_artifact(
    *,
    request: ReasoningRequest,
    provider: ReasoningProvider | None = None,
    reasoning_timestamp: datetime | None = None,
) -> ReasoningArtifact:
    return run_evidence_grounded_reasoning(
        request=request,
        provider=provider,
        reasoning_timestamp=reasoning_timestamp,
    )


def run_evidence_grounded_reasoning(
    *,
    request: ReasoningRequest,
    provider: ReasoningProvider | None = None,
    reasoning_timestamp: datetime | None = None,
) -> ReasoningArtifact:
    if request.mode is ReasoningMode.DETERMINISTIC:
        artifact = deterministic_reasoning_artifact(
            request,
            reasoning_timestamp=reasoning_timestamp,
        )
        validate_reasoning_response(
            StructuredReasoningResponse(
                reasoning_statements=artifact.reasoning_statements,
                contradictions=artifact.contradictions,
                candidate_confounders=artifact.candidate_confounders,
            ),
            request,
        )
        return artifact
    if request.mode is not ReasoningMode.PROVIDER_BACKED:
        raise UnsupportedReasoningModeError(f"unsupported reasoning mode: {request.mode}")
    return _provider_backed_reasoning(request, provider, reasoning_timestamp)


def _provider_backed_reasoning(
    request: ReasoningRequest,
    provider: ReasoningProvider | None,
    reasoning_timestamp: datetime | None,
) -> ReasoningArtifact:
    if provider is None:
        return _fallback_or_raise(
            request,
            reasoning_timestamp,
            ReasoningProviderError("missing provider"),
        )
    system_prompt, grounding_payload, _user_prompt = build_prompt_inputs(request)
    try:
        raw_response = provider.reason(
            request=request,
            system_prompt=system_prompt,
            grounding_payload=grounding_payload,
        )
        response = parse_provider_response(raw_response)
        findings = validate_reasoning_response(response, request)
        return _artifact_from_response(
            request=request,
            response=response,
            provider_name=provider.provider_name,
            validation_findings=findings,
            reasoning_timestamp=reasoning_timestamp,
        )
    except (ReasoningProviderError, ReasoningValidationError, GroundingValidationError) as exc:
        return _fallback_or_raise(request, reasoning_timestamp, exc)
    except Exception as exc:
        return _fallback_or_raise(request, reasoning_timestamp, exc)


def _fallback_or_raise(
    request: ReasoningRequest,
    reasoning_timestamp: datetime | None,
    exc: Exception,
) -> ReasoningArtifact:
    if not request.strictness.allow_provider_fallback:
        raise ReasoningProviderError(
            "provider-backed reasoning failed and fallback is disabled"
        ) from exc
    return deterministic_reasoning_artifact(
        request,
        reasoning_timestamp=reasoning_timestamp,
        deterministic_fallback_used=True,
        rejected_provider_statements=1,
        unsupported_grounding_attempts=(1 if isinstance(exc, GroundingValidationError) else 0),
        causal_guard_violations=(1 if isinstance(exc, GroundingValidationError) else 0),
    )


def _artifact_from_response(
    *,
    request: ReasoningRequest,
    response: StructuredReasoningResponse,
    provider_name: str,
    validation_findings,
    reasoning_timestamp: datetime | None,
) -> ReasoningArtifact:
    statements = tuple(sorted(response.reasoning_statements, key=lambda item: item.statement_id))
    if request.max_statement_count is not None:
        statements = statements[: request.max_statement_count]
    hypotheses = tuple(
        item for item in statements if item.category is ReasoningCategory.FOLLOW_UP_HYPOTHESIS
    )
    questions = tuple(
        item
        for item in statements
        if item.category is ReasoningCategory.FOLLOW_UP_RESEARCH_QUESTION
    )
    limitations = tuple(
        item for item in statements if item.category is ReasoningCategory.LIMITATION
    )
    grounding_summary = GroundingSummary(
        total_statements=len(statements),
        fully_grounded_statements=len(statements),
        statements_with_literature_support=sum(
            1 for item in statements if item.literature_evidence_ids
        ),
        statements_based_only_on_empirical_evidence=sum(
            1
            for item in statements
            if (item.evidence_ids or item.claim_ids) and not item.literature_evidence_ids
        ),
        plausible_or_unproven_statements=sum(
            1
            for item in statements
            if item.epistemic_status is EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN
        ),
        contradiction_count=len(response.contradictions),
        potential_confounder_count=len(response.candidate_confounders),
        follow_up_hypothesis_count=len(hypotheses),
        follow_up_research_question_count=len(questions),
        rejected_provider_statements=0,
        unsupported_grounding_attempts=0,
        causal_guard_violations=0,
    )
    content = {
        "statements": [item.model_dump(mode="json") for item in statements],
        "contradictions": [item.model_dump(mode="json") for item in response.contradictions],
        "candidate_confounders": [
            item.model_dump(mode="json") for item in response.candidate_confounders
        ],
        "provider_notes": list(response.provider_notes),
        "schema_version": REASONING_SCHEMA_VERSION,
    }
    content_digest = deterministic_id("sha256_", content).removeprefix("sha256_")
    reasoning_id = deterministic_id(
        "reasoning_",
        {
            "source_evidence_artifact_id": request.evidence_artifact.artifact_id,
            "source_coordinated_assessment_id": (
                request.coordinated_assessment.coordinated_assessment_id
            ),
            "literature_context_id": (
                request.literature_context.literature_context_id
                if request.literature_context is not None
                else None
            ),
            "provider": provider_name,
            "model_identifier": request.model_identifier,
            "content_digest_sha256": content_digest,
            "ruleset_version": REASONING_RULESET_VERSION,
            "schema_version": REASONING_SCHEMA_VERSION,
        },
    )
    timestamp = reasoning_timestamp or datetime.now(UTC)
    provenance = ReasoningProvenance(
        source_evidence_artifact_id=request.evidence_artifact.artifact_id,
        source_coordinated_assessment_id=(request.coordinated_assessment.coordinated_assessment_id),
        source_analysis_result_id=request.evidence_artifact.source_analysis_result_id,
        dataset_id=request.evidence_artifact.dataset_id,
        source_checksum_sha256=request.evidence_artifact.source_checksum_sha256,
        source_assessment_ids=request.coordinated_assessment.source_assessment_ids,
        literature_context_id=(
            request.literature_context.literature_context_id
            if request.literature_context is not None
            else None
        ),
        reasoning_mode_requested=request.mode,
        reasoning_mode_used=ReasoningMode.PROVIDER_BACKED,
        provider=provider_name,
        model_identifier=request.model_identifier,
        content_digest_sha256=content_digest,
        reasoning_timestamp=timestamp,
        software_version=request.evidence_artifact.software_version,
        phase5_schema_version=request.evidence_artifact.schema_version,
        phase7_schema_version=request.coordinated_assessment.schema_version,
        phase14_schema_version=(
            request.literature_context.schema_version
            if request.literature_context is not None
            else None
        ),
    )
    return ReasoningArtifact(
        reasoning_id=reasoning_id,
        research_question=request.research_question,
        mode=ReasoningMode.PROVIDER_BACKED,
        evidence_artifact_id=request.evidence_artifact.artifact_id,
        coordinated_assessment_id=request.coordinated_assessment.coordinated_assessment_id,
        literature_context_id=(
            request.literature_context.literature_context_id
            if request.literature_context is not None
            else None
        ),
        reasoning_statements=statements,
        contradictions=response.contradictions,
        candidate_confounders=response.candidate_confounders,
        follow_up_hypotheses=hypotheses,
        follow_up_research_questions=questions,
        limitations=limitations,
        grounding_summary=grounding_summary,
        validation_findings=validation_findings,
        provider_metadata={"provider_notes": list(response.provider_notes)},
        provenance=provenance,
        creation_timestamp=timestamp,
    )
