from evidence_helpers import run_fixture_analysis

from polaris.evidence.models import ClaimType, DescriptiveEvidenceRecord
from polaris.evidence.service import extract_evidence


def test_descriptive_extraction_numeric_categorical_and_missing_counts(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="descriptive_statistics",
        analysis_type="descriptive",
        outcome="y",
        exposures=["category"],
    )

    artifact = extract_evidence(analysis_result=result)
    descriptive = [
        record
        for record in artifact.evidence_records
        if isinstance(record, DescriptiveEvidenceRecord)
    ]
    y_record = next(record for record in descriptive if record.variable_id == "y")
    category_record = next(record for record in descriptive if record.variable_id == "category")

    assert y_record.summary_kind == "numeric"
    assert y_record.count == 8
    assert y_record.missing_count == 1
    assert y_record.mean == 10.75
    assert category_record.summary_kind == "categorical"
    assert category_record.unique_count == 4
    assert category_record.most_frequent_value == "B"
    assert category_record.source_analysis_result_id == result.result_id
    assert artifact.source_checksum_sha256 == result.source_checksum_sha256


def test_descriptive_claims_are_observations_without_direction_or_causality(
    evidence_ingestion,
):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="descriptive_statistics",
        analysis_type="descriptive",
        outcome="y",
    )
    first = extract_evidence(analysis_result=result)
    second = extract_evidence(analysis_result=result)

    assert [record.evidence_id for record in first.evidence_records] == [
        record.evidence_id for record in second.evidence_records
    ]
    claims = [
        claim
        for claim in first.claim_candidates
        if claim.claim_type is ClaimType.DESCRIPTIVE_OBSERVATION
    ]
    assert claims
    assert all(claim.causal is False for claim in claims)
    assert all(claim.supporting_evidence_ids for claim in claims)
    assert [claim.claim_id for claim in first.claim_candidates] == [
        claim.claim_id for claim in second.claim_candidates
    ]
