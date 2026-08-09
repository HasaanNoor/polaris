"""Deterministic fallback synthesis for Phase 8."""

from datetime import UTC, datetime

from polaris.agents.models import AgentDomain, UnsupportedInferenceCode
from polaris.coordination.models import CoordinatedAssessment, CoordinationCoverageStatus
from polaris.evidence.models import LimitationCode
from polaris.evidence.provenance import deterministic_id
from polaris.literature.models import LiteratureContextArtifact
from polaris.schemas.common import WarningSeverity
from polaris.synthesis.grounding import missing_domain_status
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
    UncertaintyCode,
)


def deterministic_synthesis_artifact(
    coordinated: CoordinatedAssessment,
    *,
    literature_context: LiteratureContextArtifact | None = None,
    requested_mode: SynthesisMode = SynthesisMode.DETERMINISTIC,
    synthesis_timestamp: datetime | None = None,
    extra_findings: tuple[SynthesisFinding, ...] = (),
) -> SynthesisArtifact:
    """Create a conservative deterministic synthesis from Phase 7 coordination."""

    domain_summaries = tuple(
        _domain_summary(coordinated, record.domain) for record in coordinated.domain_coverage
    )
    cross_domain_findings = _cross_domain_findings(coordinated)
    referenced_claim_ids = tuple(
        sorted({record.claim_id for record in coordinated.claim_domain_map})
    )
    referenced_evidence_ids = tuple(
        sorted({record.evidence_id for record in coordinated.evidence_domain_map})
    )
    unsupported = tuple(
        sorted(
            {record.inference_code for record in coordinated.shared_unsupported_inferences},
            key=lambda item: item.value,
        )
    )
    uncertainty = _uncertainty(coordinated)
    findings = tuple(extra_findings) + _deterministic_findings(coordinated)
    overall = _overall_summary(coordinated, literature_context=literature_context)
    limitations_summary = _limitations_summary(coordinated)
    gaps_summary = _gaps_summary(coordinated)
    digest_payload = {
        "overall_summary": overall,
        "domain_summaries": [summary.model_dump(mode="json") for summary in domain_summaries],
        "cross_domain_findings": [item.model_dump(mode="json") for item in cross_domain_findings],
        "limitations_summary": limitations_summary,
        "evidence_gaps_summary": gaps_summary,
        "unsupported": [code.value for code in unsupported],
        "uncertainty": [code.value for code in uncertainty],
    }
    content_digest = deterministic_id("sha256_", digest_payload).removeprefix("sha256_")
    synthesis_id = deterministic_id(
        "synthesis_",
        {
            "source_coordinated_assessment_id": coordinated.coordinated_assessment_id,
            "synthesis_mode": SynthesisMode.DETERMINISTIC.value,
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
        synthesis_mode_requested=requested_mode,
        synthesis_mode_used=SynthesisMode.DETERMINISTIC,
        provider=None,
        model_identifier=None,
        content_digest_sha256=content_digest,
        synthesis_timestamp=synthesis_timestamp or datetime.now(UTC),
        software_version=coordinated.provenance.software_version,
        phase5_schema_version=coordinated.provenance.phase5_schema_version,
        phase7_schema_version=coordinated.schema_version,
    )
    return SynthesisArtifact(
        synthesis_id=synthesis_id,
        source_coordinated_assessment_id=coordinated.coordinated_assessment_id,
        synthesis_mode=SynthesisMode.DETERMINISTIC,
        overall_summary=overall,
        domain_summaries=domain_summaries,
        cross_domain_findings=cross_domain_findings,
        limitations_summary=limitations_summary,
        evidence_gaps_summary=gaps_summary,
        unsupported_inferences_preserved=unsupported,
        uncertainty=uncertainty,
        referenced_claim_ids=referenced_claim_ids,
        referenced_evidence_ids=referenced_evidence_ids,
        referenced_assessment_ids=coordinated.source_assessment_ids,
        grounding_findings=findings,
        provenance=provenance,
    )


def _overall_summary(
    coordinated: CoordinatedAssessment,
    *,
    literature_context: LiteratureContextArtifact | None = None,
) -> str:
    participating = _domain_list(coordinated.participating_domains)
    missing = _domain_list(coordinated.missing_domains)
    claim_count = len(coordinated.claim_domain_map)
    evidence_count = len(coordinated.evidence_domain_map)
    sentence = (
        f"The coordinated assessment contains {evidence_count} referenced evidence records "
        f"and {claim_count} referenced non-causal claim candidates across {participating}."
    )
    if coordinated.missing_domains:
        sentence += f" Domain coverage is incomplete; {missing} was not represented."
    if coordinated.shared_unsupported_inferences:
        sentence += " Unsupported inference boundaries remain active, including causal inference."
    if literature_context is not None:
        sentence += (
            " Literature context was retrieved from a supplied local corpus and is reported "
            "separately from the empirical findings."
        )
    return sentence


def _domain_summary(coordinated: CoordinatedAssessment, domain: AgentDomain) -> DomainSynthesis:
    coverage = next(record for record in coordinated.domain_coverage if record.domain is domain)
    claim_ids = tuple(
        record.claim_id
        for record in coordinated.claim_domain_map
        if domain in record.selecting_domains
    )
    evidence_ids = tuple(
        record.evidence_id
        for record in coordinated.evidence_domain_map
        if domain in record.selecting_domains
    )
    limitations = tuple(
        sorted(
            {
                limitation
                for record in coordinated.shared_limitations
                if domain in record.domains
                for limitation in (record.limitation_code,)
            },
            key=lambda item: item.value,
        )
    )
    if coverage.coverage_status is CoordinationCoverageStatus.RELEVANT_EVIDENCE:
        summary = (
            f"{domain.value} selected {len(evidence_ids)} evidence references and "
            f"{len(claim_ids)} claim references from the coordinated assessment. "
            "These references support cautious association-oriented synthesis only."
        )
    else:
        summary = (
            f"{domain.value} was {missing_domain_status(coordinated, domain)} and should not "
            "be described as producing substantive evidence in this synthesis."
        )
    return DomainSynthesis(
        domain=domain,
        summary=summary,
        referenced_claim_ids=claim_ids,
        referenced_evidence_ids=evidence_ids,
        limitations=limitations,
        coverage_status=coverage.coverage_status,
    )


def _cross_domain_findings(coordinated: CoordinatedAssessment) -> tuple[CrossDomainSynthesis, ...]:
    findings: list[CrossDomainSynthesis] = []
    for record in coordinated.claim_domain_map:
        if record.cross_domain:
            findings.append(
                CrossDomainSynthesis(
                    finding_id=deterministic_id(
                        "cross_synthesis_",
                        {
                            "claim_id": record.claim_id,
                            "domains": [domain.value for domain in record.selecting_domains],
                            "schema_version": SYNTHESIS_SCHEMA_VERSION,
                        },
                    ),
                    summary=(
                        f"Claim {record.claim_id} appears across "
                        f"{_domain_list(record.selecting_domains)}. This indicates shared "
                        "domain relevance for the same structured non-causal claim. It is "
                        "not causal proof and not independent confirmation."
                    ),
                    domains=record.selecting_domains,
                    referenced_claim_ids=(record.claim_id,),
                )
            )
    for record in coordinated.evidence_domain_map:
        if record.cross_domain:
            findings.append(
                CrossDomainSynthesis(
                    finding_id=deterministic_id(
                        "cross_synthesis_",
                        {
                            "evidence_id": record.evidence_id,
                            "domains": [domain.value for domain in record.selecting_domains],
                            "schema_version": SYNTHESIS_SCHEMA_VERSION,
                        },
                    ),
                    summary=(
                        f"Evidence {record.evidence_id} is shared across "
                        f"{_domain_list(record.selecting_domains)}. Agreement means shared "
                        "selection of a structured reference."
                    ),
                    domains=record.selecting_domains,
                    referenced_evidence_ids=(record.evidence_id,),
                )
            )
    return tuple(sorted(findings, key=lambda item: item.finding_id))


def _limitations_summary(coordinated: CoordinatedAssessment) -> str:
    limitations = tuple(
        sorted(
            {record.limitation_code for record in coordinated.shared_limitations},
            key=lambda item: item.value,
        )
    )
    if not limitations:
        return (
            "No shared Phase 5 limitation codes were recorded, but evidence strength is not "
            "assessed by Phase 8."
        )
    return (
        "The synthesis preserves these source limitation codes: "
        f"{', '.join(code.value for code in limitations)}. "
        "They constrain interpretation and prevent causal or population-wide conclusions."
    )


def _gaps_summary(coordinated: CoordinatedAssessment) -> str:
    if not coordinated.evidence_gaps and not coordinated.domain_gaps:
        return "No Phase 7 evidence or domain gaps were recorded."
    parts = []
    if coordinated.evidence_gaps:
        parts.append(
            "evidence gaps: " + ", ".join(gap.gap_type.value for gap in coordinated.evidence_gaps)
        )
    if coordinated.domain_gaps:
        parts.append(
            "domain gaps: "
            + ", ".join(
                f"{gap.domain.value}:{gap.gap_type.value}" for gap in coordinated.domain_gaps
            )
        )
    return "The coordinated assessment records " + "; ".join(parts) + "."


def _uncertainty(coordinated: CoordinatedAssessment) -> tuple[UncertaintyCode, ...]:
    codes = {UncertaintyCode.EVIDENCE_STRENGTH_NOT_ASSESSED}
    limitations = {record.limitation_code for record in coordinated.shared_limitations}
    unsupported = {record.inference_code for record in coordinated.shared_unsupported_inferences}
    if (
        UnsupportedInferenceCode.CAUSALITY in unsupported
        or LimitationCode.OBSERVATIONAL_ASSOCIATION in limitations
    ):
        codes.add(UncertaintyCode.CAUSAL_INFERENCE_UNSUPPORTED)
    if LimitationCode.UNSUPPORTED_GENERALIZATION in limitations:
        codes.add(UncertaintyCode.GENERALIZATION_LIMITED)
    if LimitationCode.LIMITED_MODEL_SCOPE in limitations:
        codes.add(UncertaintyCode.MODEL_SCOPE_LIMITED)
    if coordinated.missing_domains or coordinated.domain_gaps:
        codes.add(UncertaintyCode.DOMAIN_COVERAGE_INCOMPLETE)
    return tuple(sorted(codes, key=lambda item: item.value))


def _deterministic_findings(coordinated: CoordinatedAssessment) -> tuple[SynthesisFinding, ...]:
    findings: list[SynthesisFinding] = []
    if coordinated.missing_domains:
        findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.MISSING_DOMAIN_ACKNOWLEDGED,
                severity=WarningSeverity.INFO,
                message="Deterministic synthesis acknowledged missing domain coverage.",
                domains=coordinated.missing_domains,
            )
        )
    if not coordinated.evidence_domain_map and not coordinated.claim_domain_map:
        findings.append(
            SynthesisFinding(
                finding_code=SynthesisFindingCode.NO_SUBSTANTIVE_EVIDENCE,
                severity=WarningSeverity.MEDIUM,
                message="No substantive evidence or claim references were available for synthesis.",
            )
        )
    return tuple(findings)


def _domain_list(domains: tuple[AgentDomain, ...]) -> str:
    if not domains:
        return "no domains"
    return ", ".join(domain.value for domain in domains)
