"""Validation for Phase 9 report inputs and generated reports."""

from collections.abc import Iterable

from polaris.coordination.models import CoordinatedAssessment
from polaris.evidence.models import EvidenceArtifact, LimitationCode
from polaris.reporting.errors import (
    ReportCompatibilityError,
    ReportReferenceError,
    ReportValidationError,
)
from polaris.reporting.models import ReportRequest, ResearchReport
from polaris.synthesis.models import SynthesisArtifact, SynthesisFindingCode
from polaris.synthesis.validation import validate_text_grounding


def validate_report_request(request: ReportRequest) -> None:
    """Verify that Phase 3-8 artifacts describe one analytical lineage."""

    synthesis = request.synthesis_artifact
    coordinated = request.coordinated_assessment
    evidence = request.evidence_artifact
    analysis = request.analysis_result
    ingestion = request.ingestion_result

    if synthesis.source_coordinated_assessment_id != coordinated.coordinated_assessment_id:
        raise ReportCompatibilityError("synthesis artifact does not reference coordinated input")
    if (
        synthesis.provenance.source_coordinated_assessment_id
        != coordinated.coordinated_assessment_id
    ):
        raise ReportCompatibilityError("synthesis provenance does not match coordinated input")
    if synthesis.provenance.source_evidence_artifact_id != evidence.artifact_id:
        raise ReportCompatibilityError("synthesis provenance does not match evidence artifact")
    if synthesis.provenance.source_analysis_result_id != analysis.result_id:
        raise ReportCompatibilityError("synthesis provenance does not match analysis result")

    if coordinated.source_evidence_artifact_id != evidence.artifact_id:
        raise ReportCompatibilityError("coordinated assessment does not reference evidence input")
    if coordinated.source_analysis_result_id != analysis.result_id:
        raise ReportCompatibilityError("coordinated assessment does not reference analysis result")
    if coordinated.dataset_id != ingestion.dataset_manifest.dataset_id:
        raise ReportCompatibilityError("coordinated dataset ID does not match ingestion result")
    if coordinated.source_checksum_sha256 != ingestion.checksum_sha256:
        raise ReportCompatibilityError(
            "coordinated source checksum does not match ingestion result"
        )

    if evidence.source_analysis_result_id != analysis.result_id:
        raise ReportCompatibilityError("evidence artifact does not reference analysis result")
    if evidence.dataset_id != ingestion.dataset_manifest.dataset_id:
        raise ReportCompatibilityError("evidence dataset ID does not match ingestion result")
    if evidence.source_checksum_sha256 != ingestion.checksum_sha256:
        raise ReportCompatibilityError("evidence checksum does not match ingestion result")

    if analysis.dataset_id != ingestion.dataset_manifest.dataset_id:
        raise ReportCompatibilityError("analysis dataset ID does not match ingestion result")
    if analysis.source_checksum_sha256 != ingestion.checksum_sha256:
        raise ReportCompatibilityError("analysis source checksum does not match ingestion result")

    _require_schema_compatibility(request)
    _validate_source_references(
        coordinated=coordinated,
        evidence=evidence,
        synthesis=synthesis,
    )


def validate_report(report: ResearchReport, request: ReportRequest) -> None:
    validate_report_request(request)
    _validate_report_references(report=report, request=request)
    _validate_preservation(report=report, request=request)
    _validate_grounding_text(report)


def _require_schema_compatibility(request: ReportRequest) -> None:
    expected = "1.0.0"
    versions = (
        request.ingestion_result.schema_version,
        request.analysis_result.schema_version,
        request.evidence_artifact.schema_version,
        request.coordinated_assessment.schema_version,
        request.synthesis_artifact.schema_version,
    )
    if any(version != expected for version in versions):
        raise ReportCompatibilityError("Phase 9 requires compatible 1.0.0 upstream schemas")


def _validate_source_references(
    *,
    coordinated: CoordinatedAssessment,
    evidence: EvidenceArtifact,
    synthesis: SynthesisArtifact,
) -> None:
    evidence_ids = {record.evidence_id for record in evidence.evidence_records}
    claim_ids = {claim.claim_id for claim in evidence.claim_candidates}
    assessment_ids = set(coordinated.source_assessment_ids)
    agreement_ids = {record.agreement_id for record in coordinated.agreements}
    divergence_ids = {record.divergence_id for record in coordinated.divergences}

    if len(evidence_ids) != len(evidence.evidence_records):
        raise ReportCompatibilityError("duplicate evidence IDs are not allowed")
    if len(claim_ids) != len(evidence.claim_candidates):
        raise ReportCompatibilityError("duplicate claim IDs are not allowed")
    if len(assessment_ids) != len(coordinated.source_assessment_ids):
        raise ReportCompatibilityError("duplicate assessment IDs are not allowed")

    for claim in evidence.claim_candidates:
        if not set(claim.supporting_evidence_ids) <= evidence_ids:
            raise ReportReferenceError("claim references missing supporting evidence IDs")
    for record in coordinated.evidence_domain_map:
        if record.evidence_id not in evidence_ids:
            raise ReportReferenceError("coordinated assessment references missing evidence IDs")
    for record in coordinated.claim_domain_map:
        if record.claim_id not in claim_ids:
            raise ReportReferenceError("coordinated assessment references missing claim IDs")
    for record in coordinated.domain_coverage:
        if record.assessment_id is not None and record.assessment_id not in assessment_ids:
            raise ReportReferenceError("domain coverage references missing assessment IDs")
    for record in coordinated.agreements:
        _validate_mixed_source_ids(record.source_ids, evidence_ids, claim_ids)
    for record in coordinated.divergences:
        _validate_mixed_source_ids(record.source_ids, evidence_ids, claim_ids)
    for record in coordinated.evidence_gaps:
        _validate_mixed_source_ids(record.source_ids, evidence_ids, claim_ids)
    if not set(synthesis.referenced_evidence_ids) <= evidence_ids:
        raise ReportReferenceError("synthesis references missing evidence IDs")
    if not set(synthesis.referenced_claim_ids) <= claim_ids:
        raise ReportReferenceError("synthesis references missing claim IDs")
    for item in synthesis.cross_domain_findings:
        if not set(item.referenced_agreement_ids) <= agreement_ids:
            raise ReportReferenceError("synthesis references missing agreement IDs")
        if not set(item.referenced_divergence_ids) <= divergence_ids:
            raise ReportReferenceError("synthesis references missing divergence IDs")


def _validate_mixed_source_ids(
    source_ids: Iterable[str], evidence_ids: set[str], claim_ids: set[str]
) -> None:
    valid = evidence_ids | claim_ids
    if not set(source_ids) <= valid:
        raise ReportReferenceError("source IDs reference missing evidence or claim IDs")


def _validate_report_references(report: ResearchReport, request: ReportRequest) -> None:
    evidence_ids = {record.evidence_id for record in request.evidence_artifact.evidence_records}
    claim_ids = {claim.claim_id for claim in request.evidence_artifact.claim_candidates}
    assessment_ids = set(request.coordinated_assessment.source_assessment_ids)
    agreement_ids = {item.agreement_id for item in request.coordinated_assessment.agreements}
    divergence_ids = {item.divergence_id for item in request.coordinated_assessment.divergences}
    gap_ids = {
        item.gap_id
        for item in (
            *request.coordinated_assessment.evidence_gaps,
            *request.coordinated_assessment.domain_gaps,
        )
    }

    for claim in report.evidence_section.claim_candidates:
        if not set(claim.supporting_evidence_ids) <= evidence_ids:
            raise ReportReferenceError("report claim references missing evidence IDs")
    for entry in report.reference_index:
        reference_id = entry.reference_id
        kind = entry.reference_kind.value
        if kind == "evidence" and reference_id not in evidence_ids:
            raise ReportReferenceError("report contains fabricated evidence reference")
        if kind == "claim" and reference_id not in claim_ids:
            raise ReportReferenceError("report contains fabricated claim reference")
        if kind == "assessment" and reference_id not in assessment_ids:
            raise ReportReferenceError("report contains fabricated assessment reference")
        if kind == "agreement" and reference_id not in agreement_ids:
            raise ReportReferenceError("report contains fabricated agreement reference")
        if kind == "divergence" and reference_id not in divergence_ids:
            raise ReportReferenceError("report contains fabricated divergence reference")
        if kind == "gap" and reference_id not in gap_ids:
            raise ReportReferenceError("report contains fabricated gap reference")


def _validate_preservation(report: ResearchReport, request: ReportRequest) -> None:
    report_limitations = set(report.limitations_section.limitation_codes)
    evidence_limitations: set[LimitationCode] = set()
    for record in request.evidence_artifact.evidence_records:
        evidence_limitations.update(record.limitation_codes)
    for claim in request.evidence_artifact.claim_candidates:
        evidence_limitations.update(claim.limitation_codes)
    for item in request.coordinated_assessment.shared_limitations:
        evidence_limitations.add(item.limitation_code)
    if not evidence_limitations <= report_limitations:
        raise ReportValidationError("report omitted upstream limitations")

    unsupported = {
        item.inference_code for item in request.coordinated_assessment.shared_unsupported_inferences
    } | set(request.synthesis_artifact.unsupported_inferences_preserved)
    if not unsupported <= set(report.unsupported_inferences_section.unsupported_inferences):
        raise ReportValidationError("report omitted unsupported-inference boundaries")

    represented_domains = {
        item.domain
        for item in report.domain_assessments_section.domains
        if not item.assessment_supplied
    }
    if not set(request.coordinated_assessment.missing_domains) <= represented_domains:
        raise ReportValidationError("report omitted missing domain representation")


def _validate_grounding_text(report: ResearchReport) -> None:
    findings = validate_text_grounding(_report_text_parts(report))
    blocked = tuple(
        finding
        for finding in findings
        if finding.finding_code
        in {
            SynthesisFindingCode.CAUSAL_LANGUAGE_VIOLATION,
            SynthesisFindingCode.POLICY_RECOMMENDATION_VIOLATION,
            SynthesisFindingCode.MEDICAL_RECOMMENDATION_VIOLATION,
        }
    )
    if blocked:
        raise ReportValidationError("report text introduced prohibited overreach language")


def _report_text_parts(report: ResearchReport) -> tuple[str, ...]:
    parts = [
        report.title,
        report.subtitle or "",
        report.executive_summary,
        report.synthesis_section.overall_summary,
        report.synthesis_section.limitations_summary,
        report.synthesis_section.evidence_gaps_summary,
        report.limitations_section.narrative_summary,
    ]
    parts.extend(summary["summary"] for summary in report.synthesis_section.domain_summaries)
    parts.extend(item["summary"] for item in report.synthesis_section.cross_domain_findings)
    return tuple(parts)
