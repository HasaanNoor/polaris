"""Structured response and grounding validation for Phase 8 synthesis."""

import re
from collections.abc import Iterable

from pydantic import ValidationError

from polaris.coordination.models import CoordinatedAssessment, CoordinationCoverageStatus
from polaris.schemas.common import WarningSeverity
from polaris.synthesis.errors import GroundingValidationError, SynthesisValidationError
from polaris.synthesis.grounding import source_reference_sets
from polaris.synthesis.models import (
    StructuredSynthesisResponse,
    SynthesisArtifact,
    SynthesisFinding,
    SynthesisFindingCode,
)

_POSITIVE_CAUSAL_PATTERNS = (
    re.compile(r"\bcauses?\b", re.IGNORECASE),
    re.compile(r"\bcaused\b", re.IGNORECASE),
    re.compile(r"\bleads?\s+to\b", re.IGNORECASE),
    re.compile(r"\bresults?\s+in\b", re.IGNORECASE),
    re.compile(r"\bdrives?\b", re.IGNORECASE),
    re.compile(r"\bproduces?\b", re.IGNORECASE),
    re.compile(r"\bdetermines?\b", re.IGNORECASE),
    re.compile(r"\bimpact\s+of\b", re.IGNORECASE),
    re.compile(r"\beffect\s+of\b", re.IGNORECASE),
    re.compile(r"\bproves?\b", re.IGNORECASE),
    re.compile(r"\bthe mechanism is\b", re.IGNORECASE),
)
_ALLOWED_CAUSAL_CONTEXTS = (
    "causal inference is unsupported",
    "causality is unsupported",
    "causal interpretation is unsupported",
    "does not support causality",
    "does not establish causation",
    "causal claims are unsupported",
    "unsupported causal inference",
)
_POLICY_PATTERNS = (
    re.compile(r"\bpolicy should\b", re.IGNORECASE),
    re.compile(r"\bpolicies should\b", re.IGNORECASE),
    re.compile(r"\bgovernments? must\b", re.IGNORECASE),
    re.compile(r"\bshould implement\b", re.IGNORECASE),
    re.compile(r"\bmust implement\b", re.IGNORECASE),
    re.compile(r"\brecommend(?:s|ed|ation)?\b", re.IGNORECASE),
)
_MEDICAL_PATTERNS = (
    re.compile(r"\bmedical advice\b", re.IGNORECASE),
    re.compile(r"\bclinicians? should\b", re.IGNORECASE),
    re.compile(r"\bpatients? should\b", re.IGNORECASE),
    re.compile(r"\btreatment should\b", re.IGNORECASE),
    re.compile(r"\bdiagnos(?:e|is)\b", re.IGNORECASE),
)


def parse_provider_response(
    response: StructuredSynthesisResponse | dict,
) -> StructuredSynthesisResponse:
    if isinstance(response, StructuredSynthesisResponse):
        return response
    try:
        return StructuredSynthesisResponse.model_validate(response)
    except ValidationError as exc:
        raise SynthesisValidationError("provider returned malformed structured synthesis") from exc


def validate_provider_response(
    response: StructuredSynthesisResponse,
    coordinated: CoordinatedAssessment,
) -> tuple[SynthesisFinding, ...]:
    findings: list[SynthesisFinding] = []
    _validate_references(response, coordinated, findings)
    _validate_required_limitations(response, coordinated, findings)
    _validate_preserved_unsupported(response, coordinated, findings)
    _validate_missing_domains(response, coordinated, findings)
    findings.extend(validate_text_grounding(_all_response_text(response)))
    if any(finding.severity is WarningSeverity.HIGH for finding in findings):
        raise GroundingValidationError("provider synthesis failed grounding validation")
    return tuple(findings)


def validate_artifact_grounding(
    artifact: SynthesisArtifact,
    coordinated: CoordinatedAssessment,
) -> tuple[SynthesisFinding, ...]:
    findings: list[SynthesisFinding] = []
    _validate_artifact_references(artifact, coordinated, findings)
    findings.extend(validate_text_grounding(_all_artifact_text(artifact)))
    if any(finding.severity is WarningSeverity.HIGH for finding in findings):
        raise GroundingValidationError("synthesis artifact failed grounding validation")
    return tuple(findings)


def validate_text_grounding(text_parts: Iterable[str]) -> tuple[SynthesisFinding, ...]:
    text = "\n".join(part for part in text_parts if part).strip()
    if not text:
        return (
            SynthesisFinding(
                finding_code=SynthesisFindingCode.LLM_RESPONSE_INVALID,
                severity=WarningSeverity.HIGH,
                message="Synthesis text is empty.",
            ),
        )
    findings: list[SynthesisFinding] = []
    normalized = text.lower()
    causal_text = normalized
    for allowed in _ALLOWED_CAUSAL_CONTEXTS:
        causal_text = causal_text.replace(allowed, "")
    if any(pattern.search(causal_text) for pattern in _POSITIVE_CAUSAL_PATTERNS):
        findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.CAUSAL_LANGUAGE_VIOLATION,
                severity=WarningSeverity.HIGH,
                message="Synthesis introduced unsupported positive causal language.",
            )
        )
    if any(pattern.search(text) for pattern in _POLICY_PATTERNS):
        findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.POLICY_RECOMMENDATION_VIOLATION,
                severity=WarningSeverity.HIGH,
                message="Synthesis introduced prohibited policy recommendation language.",
            )
        )
    if any(pattern.search(text) for pattern in _MEDICAL_PATTERNS):
        findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.MEDICAL_RECOMMENDATION_VIOLATION,
                severity=WarningSeverity.HIGH,
                message="Synthesis introduced prohibited medical recommendation language.",
            )
        )
    return tuple(findings)


def _validate_references(
    response: StructuredSynthesisResponse,
    coordinated: CoordinatedAssessment,
    findings: list[SynthesisFinding],
) -> None:
    (
        claim_ids,
        evidence_ids,
        _assessment_ids,
        agreement_ids,
        divergence_ids,
        participating,
        missing,
    ) = source_reference_sets(coordinated)
    no_evidence_domains = {
        record.domain
        for record in coordinated.domain_coverage
        if record.coverage_status
        in {
            CoordinationCoverageStatus.ASSESSMENT_MISSING,
            CoordinationCoverageStatus.NO_RELEVANT_EVIDENCE,
        }
    }
    response_claims = set(response.referenced_claim_ids)
    response_evidence = set(response.referenced_evidence_ids)
    for domain_summary in response.domain_summaries:
        response_claims.update(domain_summary.referenced_claim_ids)
        response_evidence.update(domain_summary.referenced_evidence_ids)
        if domain_summary.domain not in participating | missing:
            _fabricated(f"Unknown domain {domain_summary.domain}.", findings)
        if domain_summary.domain in no_evidence_domains and (
            domain_summary.referenced_claim_ids or domain_summary.referenced_evidence_ids
        ):
            _fabricated(
                "Domain without relevant evidence was described with evidence references.",
                findings,
            )
    for item in response.cross_domain_findings:
        response_claims.update(item.referenced_claim_ids)
        response_evidence.update(item.referenced_evidence_ids)
        if not set(item.referenced_agreement_ids) <= agreement_ids:
            _fabricated("Cross-domain finding referenced fabricated agreement IDs.", findings)
        if not set(item.referenced_divergence_ids) <= divergence_ids:
            _fabricated("Cross-domain finding referenced fabricated divergence IDs.", findings)
        if not set(item.domains) <= participating | missing:
            _fabricated("Cross-domain finding referenced unknown domains.", findings)
    if not response_claims <= claim_ids:
        _fabricated("Synthesis referenced fabricated claim IDs.", findings)
    if not response_evidence <= evidence_ids:
        _fabricated("Synthesis referenced fabricated evidence IDs.", findings)


def _validate_artifact_references(
    artifact: SynthesisArtifact,
    coordinated: CoordinatedAssessment,
    findings: list[SynthesisFinding],
) -> None:
    claim_ids, evidence_ids, assessment_ids, *_ = source_reference_sets(coordinated)
    if not set(artifact.referenced_claim_ids) <= claim_ids:
        _fabricated("Synthesis artifact referenced fabricated claim IDs.", findings)
    if not set(artifact.referenced_evidence_ids) <= evidence_ids:
        _fabricated("Synthesis artifact referenced fabricated evidence IDs.", findings)
    if not set(artifact.referenced_assessment_ids) <= assessment_ids:
        _fabricated("Synthesis artifact referenced fabricated assessment IDs.", findings)


def _validate_required_limitations(
    response: StructuredSynthesisResponse,
    coordinated: CoordinatedAssessment,
    findings: list[SynthesisFinding],
) -> None:
    required = {record.limitation_code for record in coordinated.shared_limitations}
    mentioned = set()
    for summary in response.domain_summaries:
        mentioned.update(summary.limitations)
    text = _lower_join(_all_response_text(response))
    omitted = tuple(
        code
        for code in sorted(required, key=lambda item: item.value)
        if code not in mentioned and code.value.lower() not in text
    )
    if omitted:
        findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.LIMITATION_OMITTED,
                severity=WarningSeverity.HIGH,
                message="Synthesis omitted required source limitations.",
                source_ids=tuple(code.value for code in omitted),
            )
        )


def _validate_preserved_unsupported(
    response: StructuredSynthesisResponse,
    coordinated: CoordinatedAssessment,
    findings: list[SynthesisFinding],
) -> None:
    required = {record.inference_code for record in coordinated.shared_unsupported_inferences}
    if not required <= set(response.unsupported_inferences_preserved):
        missing = tuple(sorted(required - set(response.unsupported_inferences_preserved)))
        findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.UNSUPPORTED_INFERENCE_DETECTED,
                severity=WarningSeverity.HIGH,
                message="Synthesis failed to preserve unsupported-inference boundaries.",
                source_ids=tuple(code.value for code in missing),
            )
        )


def _validate_missing_domains(
    response: StructuredSynthesisResponse,
    coordinated: CoordinatedAssessment,
    findings: list[SynthesisFinding],
) -> None:
    missing = set(coordinated.missing_domains)
    summarized = {summary.domain for summary in response.domain_summaries}
    if missing and missing <= summarized:
        findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.MISSING_DOMAIN_ACKNOWLEDGED,
                severity=WarningSeverity.INFO,
                message="Synthesis acknowledged missing domain coverage.",
                domains=tuple(missing),
            )
        )


def _fabricated(message: str, findings: list[SynthesisFinding]) -> None:
    findings.append(
        SynthesisFinding(
            finding_code=SynthesisFindingCode.FABRICATED_REFERENCE,
            severity=WarningSeverity.HIGH,
            message=message,
        )
    )


def _all_response_text(response: StructuredSynthesisResponse) -> tuple[str, ...]:
    return (
        response.overall_summary,
        response.limitations_summary,
        response.evidence_gaps_summary,
        *(summary.summary for summary in response.domain_summaries),
        *(item.summary for item in response.cross_domain_findings),
    )


def _all_artifact_text(artifact: SynthesisArtifact) -> tuple[str, ...]:
    return (
        artifact.overall_summary,
        artifact.limitations_summary,
        artifact.evidence_gaps_summary,
        *(summary.summary for summary in artifact.domain_summaries),
        *(item.summary for item in artifact.cross_domain_findings),
    )


def _lower_join(parts: Iterable[str]) -> str:
    return "\n".join(parts).lower()
