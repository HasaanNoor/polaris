from evidence_helpers import run_fixture_analysis

from polaris.evidence.models import (
    ClaimType,
    CorrelationEvidenceRecord,
    Direction,
    LimitationCode,
)
from polaris.evidence.service import extract_evidence


def test_positive_pearson_evidence_and_association_claim(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="pearson_correlation",
        analysis_type="correlation",
        outcome="y",
        exposures=["x"],
    )

    artifact = extract_evidence(analysis_result=result)
    record = _first_correlation(artifact)
    claim = next(
        claim for claim in artifact.claim_candidates if claim.claim_type is ClaimType.ASSOCIATION
    )

    assert record.method == "pearson"
    assert record.direction is Direction.POSITIVE
    assert record.p_value is not None
    assert record.observation_count == 8
    assert record.missing_exclusion_count == 1
    assert claim.direction is Direction.POSITIVE
    assert claim.causal is False
    assert claim.supporting_evidence_ids == (record.evidence_id,)
    assert LimitationCode.OBSERVATIONAL_ASSOCIATION in claim.limitation_codes
    assert LimitationCode.UNSUPPORTED_GENERALIZATION in claim.limitation_codes


def test_negative_spearman_and_perfect_correlation_limitation(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="spearman_correlation",
        analysis_type="correlation",
        outcome="y",
        exposures=["negative_x"],
    )

    artifact = extract_evidence(analysis_result=result)
    record = _first_correlation(artifact)
    claim = next(
        claim for claim in artifact.claim_candidates if claim.claim_type is ClaimType.ASSOCIATION
    )

    assert record.method == "spearman"
    assert record.direction is Direction.NEGATIVE
    assert LimitationCode.PERFECT_CORRELATION in record.limitation_codes
    assert LimitationCode.PERFECT_CORRELATION in claim.limitation_codes


def test_undefined_and_zero_correlation_direction(evidence_ingestion):
    undefined = run_fixture_analysis(
        evidence_ingestion,
        procedure="pearson_correlation",
        analysis_type="correlation",
        outcome="x",
        exposures=["constant"],
    )
    undefined_artifact = extract_evidence(analysis_result=undefined)
    undefined_record = _first_correlation(undefined_artifact)
    assert undefined_record.direction is Direction.UNDEFINED
    assert not any(
        claim.claim_type is ClaimType.ASSOCIATION for claim in undefined_artifact.claim_candidates
    )

    zero_record = CorrelationEvidenceRecord(
        evidence_id="evidence_zero",
        source_analysis_result_id="analysis",
        dataset_id="dataset",
        source_checksum_sha256="abc",
        statistical_procedure="pearson_correlation",
        sample_size=3,
        provenance=undefined_artifact.provenance,
        variable_id_1="x",
        variable_id_2="y",
        method="pearson",
        correlation_coefficient=0.0,
        p_value=1.0,
        observation_count=3,
        defined=True,
        direction=Direction.ZERO,
        missing_exclusion_count=0,
    )
    assert zero_record.direction is Direction.ZERO


def _first_correlation(artifact) -> CorrelationEvidenceRecord:
    return next(
        record
        for record in artifact.evidence_records
        if isinstance(record, CorrelationEvidenceRecord)
    )
