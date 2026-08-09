"""Public API for Phase 8 synthesis."""

import hashlib
import json
from datetime import UTC, datetime

from polaris.evidence.provenance import deterministic_id
from polaris.schemas.common import WarningSeverity
from polaris.synthesis.deterministic import deterministic_synthesis_artifact
from polaris.synthesis.errors import (
    GroundingValidationError,
    SynthesisProviderError,
    SynthesisValidationError,
    UnsupportedSynthesisModeError,
)
from polaris.synthesis.models import (
    SYNTHESIS_RULESET_VERSION,
    SYNTHESIS_SCHEMA_VERSION,
    CrossDomainSynthesis,
    DomainSynthesis,
    SynthesisArtifact,
    SynthesisFinding,
    SynthesisFindingCode,
    SynthesisMode,
    SynthesisProvenance,
    SynthesisRequest,
)
from polaris.synthesis.prompts import build_prompt_inputs
from polaris.synthesis.provider import SynthesisProvider
from polaris.synthesis.validation import parse_provider_response, validate_provider_response


def synthesize_assessment(
    *,
    request: SynthesisRequest,
    provider: SynthesisProvider | None = None,
    synthesis_timestamp: datetime | None = None,
) -> SynthesisArtifact:
    """Produce a Phase 8 synthesis artifact from a Phase 7 coordinated assessment."""

    if request.mode is SynthesisMode.DETERMINISTIC:
        return deterministic_synthesis_artifact(
            request.coordinated_assessment,
            literature_context=request.literature_context,
            requested_mode=request.mode,
            synthesis_timestamp=synthesis_timestamp,
        )
    if request.mode is not SynthesisMode.LLM:
        raise UnsupportedSynthesisModeError(f"unsupported synthesis mode: {request.mode}")
    return _llm_synthesis(request, provider=provider, synthesis_timestamp=synthesis_timestamp)


def _llm_synthesis(
    request: SynthesisRequest,
    *,
    provider: SynthesisProvider | None,
    synthesis_timestamp: datetime | None,
) -> SynthesisArtifact:
    fallback_findings: list[SynthesisFinding] = []
    if provider is None:
        fallback_findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.LLM_PROVIDER_UNAVAILABLE,
                severity=WarningSeverity.HIGH,
                message="LLM synthesis requested but no provider was supplied.",
            )
        )
        return _fallback_or_raise(request, tuple(fallback_findings), synthesis_timestamp)
    system_prompt, grounding_payload, _user_prompt = build_prompt_inputs(request)
    try:
        raw_response = provider.synthesize(
            request=request,
            system_prompt=system_prompt,
            grounding_payload=grounding_payload,
        )
        response = parse_provider_response(raw_response)
        validation_findings = validate_provider_response(response, request.coordinated_assessment)
        return _artifact_from_response(
            request=request,
            response=response,
            provider_name=provider.provider_name,
            validation_findings=validation_findings,
            synthesis_timestamp=synthesis_timestamp,
        )
    except (SynthesisProviderError, SynthesisValidationError, GroundingValidationError) as exc:
        fallback_findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.LLM_RESPONSE_INVALID,
                severity=WarningSeverity.HIGH,
                message=f"LLM synthesis failed validation: {exc}",
            )
        )
        return _fallback_or_raise(request, tuple(fallback_findings), synthesis_timestamp, exc)
    except Exception as exc:
        fallback_findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.LLM_PROVIDER_UNAVAILABLE,
                severity=WarningSeverity.HIGH,
                message=f"LLM provider failed: {exc}",
            )
        )
        return _fallback_or_raise(request, tuple(fallback_findings), synthesis_timestamp, exc)


def _fallback_or_raise(
    request: SynthesisRequest,
    findings: tuple[SynthesisFinding, ...],
    synthesis_timestamp: datetime | None,
    exc: Exception | None = None,
) -> SynthesisArtifact:
    if not request.allow_deterministic_fallback:
        raise SynthesisProviderError("LLM synthesis failed and fallback is disabled") from exc
    fallback_finding = SynthesisFinding(
        finding_code=SynthesisFindingCode.FALLBACK_USED,
        severity=WarningSeverity.MEDIUM,
        message="Deterministic synthesis fallback was used after LLM synthesis failure.",
    )
    return deterministic_synthesis_artifact(
        request.coordinated_assessment,
        literature_context=request.literature_context,
        requested_mode=request.mode,
        synthesis_timestamp=synthesis_timestamp,
        extra_findings=(*findings, fallback_finding),
    )


def _artifact_from_response(
    *,
    request: SynthesisRequest,
    response,
    provider_name: str,
    validation_findings: tuple[SynthesisFinding, ...],
    synthesis_timestamp: datetime | None,
) -> SynthesisArtifact:
    coordinated = request.coordinated_assessment
    coverage = {record.domain: record.coverage_status for record in coordinated.domain_coverage}
    domain_summaries = tuple(
        DomainSynthesis(
            domain=item.domain,
            summary=item.summary,
            referenced_claim_ids=item.referenced_claim_ids,
            referenced_evidence_ids=item.referenced_evidence_ids,
            limitations=item.limitations,
            coverage_status=coverage[item.domain],
        )
        for item in response.domain_summaries
    )
    cross_domain_findings = tuple(
        CrossDomainSynthesis(
            finding_id=deterministic_id(
                "cross_synthesis_",
                {
                    "summary": item.summary,
                    "domains": [domain.value for domain in item.domains],
                    "claim_ids": item.referenced_claim_ids,
                    "evidence_ids": item.referenced_evidence_ids,
                    "agreement_ids": item.referenced_agreement_ids,
                    "divergence_ids": item.referenced_divergence_ids,
                    "schema_version": SYNTHESIS_SCHEMA_VERSION,
                },
            ),
            summary=item.summary,
            domains=item.domains,
            referenced_claim_ids=item.referenced_claim_ids,
            referenced_evidence_ids=item.referenced_evidence_ids,
            referenced_agreement_ids=item.referenced_agreement_ids,
            referenced_divergence_ids=item.referenced_divergence_ids,
        )
        for item in response.cross_domain_findings
    )
    referenced_claim_ids = tuple(
        sorted(
            set(response.referenced_claim_ids)
            | {claim for item in domain_summaries for claim in item.referenced_claim_ids}
            | {claim for item in cross_domain_findings for claim in item.referenced_claim_ids}
        )
    )
    referenced_evidence_ids = tuple(
        sorted(
            set(response.referenced_evidence_ids)
            | {evidence for item in domain_summaries for evidence in item.referenced_evidence_ids}
            | {
                evidence
                for item in cross_domain_findings
                for evidence in item.referenced_evidence_ids
            }
        )
    )
    content = {
        "overall_summary": response.overall_summary,
        "domain_summaries": [item.model_dump(mode="json") for item in domain_summaries],
        "cross_domain_findings": [item.model_dump(mode="json") for item in cross_domain_findings],
        "limitations_summary": response.limitations_summary,
        "evidence_gaps_summary": response.evidence_gaps_summary,
        "unsupported": [code.value for code in response.unsupported_inferences_preserved],
        "uncertainty": [code.value for code in response.uncertainty],
    }
    content_json = json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False)
    content_digest = hashlib.sha256(content_json.encode("utf-8")).hexdigest()
    synthesis_id = deterministic_id(
        "synthesis_run_",
        {
            "source_coordinated_assessment_id": coordinated.coordinated_assessment_id,
            "provider": provider_name,
            "model_identifier": request.model_identifier,
            "content_digest_sha256": content_digest,
            "ruleset_version": SYNTHESIS_RULESET_VERSION,
            "schema_version": SYNTHESIS_SCHEMA_VERSION,
        },
    )
    provenance = SynthesisProvenance(
        source_coordinated_assessment_id=coordinated.coordinated_assessment_id,
        source_evidence_artifact_id=coordinated.source_evidence_artifact_id,
        source_analysis_result_id=coordinated.source_analysis_result_id,
        dataset_id=coordinated.dataset_id,
        source_checksum_sha256=coordinated.source_checksum_sha256,
        source_assessment_ids=coordinated.source_assessment_ids,
        synthesis_mode_requested=request.mode,
        synthesis_mode_used=SynthesisMode.LLM,
        provider=provider_name,
        model_identifier=request.model_identifier,
        content_digest_sha256=content_digest,
        synthesis_timestamp=synthesis_timestamp or datetime.now(UTC),
        software_version=coordinated.provenance.software_version,
        phase5_schema_version=coordinated.provenance.phase5_schema_version,
        phase7_schema_version=coordinated.schema_version,
    )
    return SynthesisArtifact(
        synthesis_id=synthesis_id,
        source_coordinated_assessment_id=coordinated.coordinated_assessment_id,
        synthesis_mode=SynthesisMode.LLM,
        overall_summary=response.overall_summary,
        domain_summaries=domain_summaries,
        cross_domain_findings=cross_domain_findings,
        limitations_summary=response.limitations_summary,
        evidence_gaps_summary=response.evidence_gaps_summary,
        unsupported_inferences_preserved=response.unsupported_inferences_preserved,
        uncertainty=response.uncertainty,
        referenced_claim_ids=referenced_claim_ids,
        referenced_evidence_ids=referenced_evidence_ids,
        referenced_assessment_ids=coordinated.source_assessment_ids,
        grounding_findings=validation_findings,
        provenance=provenance,
    )
