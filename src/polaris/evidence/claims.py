"""Deterministic claim candidate generation from structured evidence records."""

from collections.abc import Iterable
from datetime import datetime

from polaris.analysis.models import AnalysisResult
from polaris.evidence.extractors import merge_limitations
from polaris.evidence.models import (
    ClaimCandidate,
    ClaimType,
    CorrelationEvidenceRecord,
    DescriptiveEvidenceRecord,
    DiagnosticEvidenceRecord,
    Direction,
    EvidenceRecord,
    EvidenceType,
    LimitationCode,
    ModelFitEvidenceRecord,
    RegressionCoefficientEvidenceRecord,
)
from polaris.evidence.provenance import claim_id, evidence_provenance


def generate_claim_candidates(
    analysis_result: AnalysisResult,
    evidence_records: Iterable[EvidenceRecord],
    *,
    extraction_timestamp: datetime | None = None,
) -> tuple[ClaimCandidate, ...]:
    provenance = evidence_provenance(analysis_result, extraction_timestamp=extraction_timestamp)
    evidence = tuple(evidence_records)
    global_limitations = _global_limitations(evidence)
    claims: list[ClaimCandidate] = []

    for record in evidence:
        if isinstance(record, DescriptiveEvidenceRecord):
            claims.append(_descriptive_claim(record, analysis_result, provenance))
        elif isinstance(record, CorrelationEvidenceRecord):
            if record.defined:
                claims.append(
                    _correlation_claim(record, analysis_result, provenance, global_limitations)
                )
        elif isinstance(record, RegressionCoefficientEvidenceRecord):
            if not record.is_intercept:
                claims.append(
                    _regression_claim(record, analysis_result, provenance, global_limitations)
                )
            if _has_uncertainty(record):
                claims.append(_uncertainty_claim(record, analysis_result, provenance))
        elif isinstance(record, DiagnosticEvidenceRecord | ModelFitEvidenceRecord):
            if record.limitation_codes:
                claims.append(_limitation_claim(record, analysis_result, provenance))

    deduplicated = {claim.claim_id: claim for claim in claims}
    return tuple(sorted(deduplicated.values(), key=lambda claim: claim.claim_id))


def _descriptive_claim(record, analysis_result, provenance) -> ClaimCandidate:
    payload = {
        "claim_type": ClaimType.DESCRIPTIVE_OBSERVATION,
        "supporting_evidence_ids": (record.evidence_id,),
        "subject_variable": record.variable_id,
        "direction": Direction.NOT_APPLICABLE,
    }
    return ClaimCandidate(
        claim_id=claim_id(payload),
        claim_type=ClaimType.DESCRIPTIVE_OBSERVATION,
        subject_variable=record.variable_id,
        direction=Direction.NOT_APPLICABLE,
        statistical_procedure=analysis_result.analysis_method,
        supporting_evidence_ids=(record.evidence_id,),
        limitation_codes=record.limitation_codes,
        source_analysis_result_id=analysis_result.result_id,
        dataset_id=analysis_result.dataset_id,
        provenance=provenance,
    )


def _correlation_claim(
    record,
    analysis_result,
    provenance,
    global_limitations,
) -> ClaimCandidate:
    limitations = merge_limitations(
        record.limitation_codes,
        global_limitations,
        (
            LimitationCode.OBSERVATIONAL_ASSOCIATION,
            LimitationCode.UNSUPPORTED_GENERALIZATION,
        ),
    )
    payload = {
        "claim_type": ClaimType.ASSOCIATION,
        "supporting_evidence_ids": (record.evidence_id,),
        "subject_variable": record.variable_id_1,
        "outcome_variable": record.variable_id_2,
        "direction": record.direction,
    }
    return ClaimCandidate(
        claim_id=claim_id(payload),
        claim_type=ClaimType.ASSOCIATION,
        subject_variable=record.variable_id_1,
        outcome_variable=record.variable_id_2,
        related_variables=(record.variable_id_1, record.variable_id_2),
        direction=record.direction,
        statistical_procedure=analysis_result.analysis_method,
        supporting_evidence_ids=(record.evidence_id,),
        limitation_codes=limitations,
        source_analysis_result_id=analysis_result.result_id,
        dataset_id=analysis_result.dataset_id,
        provenance=provenance,
    )


def _regression_claim(
    record,
    analysis_result,
    provenance,
    global_limitations,
) -> ClaimCandidate:
    limitations = merge_limitations(
        record.limitation_codes,
        global_limitations,
        (
            LimitationCode.LIMITED_MODEL_SCOPE,
            LimitationCode.OBSERVATIONAL_ASSOCIATION,
            LimitationCode.UNSUPPORTED_GENERALIZATION,
        ),
    )
    payload = {
        "claim_type": ClaimType.CONDITIONAL_ASSOCIATION,
        "supporting_evidence_ids": (record.evidence_id,),
        "subject_variable": record.variable_id,
        "outcome_variable": record.dependent_variable_id,
        "related_variables": record.predictor_variable_ids,
        "direction": record.direction,
    }
    return ClaimCandidate(
        claim_id=claim_id(payload),
        claim_type=ClaimType.CONDITIONAL_ASSOCIATION,
        subject_variable=record.variable_id,
        outcome_variable=record.dependent_variable_id,
        related_variables=record.predictor_variable_ids,
        direction=record.direction,
        statistical_procedure=analysis_result.analysis_method,
        supporting_evidence_ids=(record.evidence_id,),
        limitation_codes=limitations,
        source_analysis_result_id=analysis_result.result_id,
        dataset_id=analysis_result.dataset_id,
        provenance=provenance,
        p_value_below_threshold=record.below_significance_threshold,
        confidence_interval_crosses_zero=_interval_crosses_zero(record),
    )


def _uncertainty_claim(record, analysis_result, provenance) -> ClaimCandidate:
    payload = {
        "claim_type": ClaimType.STATISTICAL_UNCERTAINTY,
        "supporting_evidence_ids": (record.evidence_id,),
        "subject_variable": record.variable_id,
        "outcome_variable": record.dependent_variable_id,
        "direction": Direction.NOT_APPLICABLE,
        "p_value_below_threshold": record.below_significance_threshold,
        "confidence_interval_crosses_zero": _interval_crosses_zero(record),
    }
    return ClaimCandidate(
        claim_id=claim_id(payload),
        claim_type=ClaimType.STATISTICAL_UNCERTAINTY,
        subject_variable=record.variable_id,
        outcome_variable=record.dependent_variable_id,
        related_variables=record.predictor_variable_ids,
        direction=Direction.NOT_APPLICABLE,
        statistical_procedure=analysis_result.analysis_method,
        supporting_evidence_ids=(record.evidence_id,),
        limitation_codes=record.limitation_codes,
        source_analysis_result_id=analysis_result.result_id,
        dataset_id=analysis_result.dataset_id,
        provenance=provenance,
        p_value_below_threshold=record.below_significance_threshold,
        confidence_interval_crosses_zero=_interval_crosses_zero(record),
    )


def _limitation_claim(record, analysis_result, provenance) -> ClaimCandidate:
    subject = getattr(record, "variable_id", None)
    if isinstance(record, ModelFitEvidenceRecord):
        subject = record.dependent_variable_id
    payload = {
        "claim_type": ClaimType.MODEL_LIMITATION,
        "supporting_evidence_ids": (record.evidence_id,),
        "subject_variable": subject,
        "direction": Direction.NOT_APPLICABLE,
        "limitations": record.limitation_codes,
    }
    return ClaimCandidate(
        claim_id=claim_id(payload),
        claim_type=ClaimType.MODEL_LIMITATION,
        subject_variable=subject,
        direction=Direction.NOT_APPLICABLE,
        statistical_procedure=analysis_result.analysis_method,
        supporting_evidence_ids=(record.evidence_id,),
        limitation_codes=record.limitation_codes,
        source_analysis_result_id=analysis_result.result_id,
        dataset_id=analysis_result.dataset_id,
        provenance=provenance,
    )


def _has_uncertainty(record: RegressionCoefficientEvidenceRecord) -> bool:
    return (
        record.below_significance_threshold is not None
        or _interval_crosses_zero(record) is not None
    )


def _interval_crosses_zero(record: RegressionCoefficientEvidenceRecord) -> bool | None:
    if record.confidence_interval_low is None or record.confidence_interval_high is None:
        return None
    return record.confidence_interval_low <= 0 <= record.confidence_interval_high


def _global_limitations(evidence: Iterable[EvidenceRecord]) -> tuple[LimitationCode, ...]:
    values: list[LimitationCode] = []
    for record in evidence:
        if record.evidence_type is EvidenceType.SAMPLE_QUALITY:
            values.extend(record.limitation_codes)
        if isinstance(record, DiagnosticEvidenceRecord | ModelFitEvidenceRecord):
            values.extend(record.limitation_codes)
    return merge_limitations(tuple(values))
