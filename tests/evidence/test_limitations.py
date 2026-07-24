from evidence_helpers import run_fixture_analysis

from polaris.evidence.models import (
    ClaimType,
    LimitationCode,
    SampleQualityEvidenceRecord,
)
from polaris.evidence.service import extract_evidence


def test_sample_quality_records_missing_data_exclusions(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="ordinary_least_squares",
        analysis_type="regression",
        model_family="linear",
        outcome="y",
        exposures=["x"],
        covariates=["z"],
    )

    artifact = extract_evidence(analysis_result=result)
    sample = next(
        record
        for record in artifact.evidence_records
        if isinstance(record, SampleQualityEvidenceRecord)
    )

    assert sample.original_accepted_record_count == 9
    assert sample.final_analysis_sample_size == 7
    assert sample.excluded_row_count == 2
    assert sample.missing_value_exclusion_count == 2
    assert sample.accepted_records_used_percentage == 7 / 9 * 100.0
    assert LimitationCode.MISSING_DATA_EXCLUSION in sample.limitation_codes


def test_no_missing_data_limitation_when_no_rows_excluded(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="ordinary_least_squares",
        analysis_type="regression",
        model_family="linear",
        outcome="x",
        exposures=["negative_x"],
    )

    artifact = extract_evidence(analysis_result=result)
    sample = next(
        record
        for record in artifact.evidence_records
        if isinstance(record, SampleQualityEvidenceRecord)
    )

    assert sample.excluded_row_count == 0
    assert LimitationCode.MISSING_DATA_EXCLUSION not in sample.limitation_codes


def test_limitations_are_attached_to_claims_without_invention(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="pearson_correlation",
        analysis_type="correlation",
        outcome="x",
        exposures=["negative_x"],
    )

    artifact = extract_evidence(analysis_result=result)
    claim = next(
        claim for claim in artifact.claim_candidates if claim.claim_type is ClaimType.ASSOCIATION
    )

    assert LimitationCode.OBSERVATIONAL_ASSOCIATION in claim.limitation_codes
    assert LimitationCode.UNSUPPORTED_GENERALIZATION in claim.limitation_codes
    assert LimitationCode.MISSING_DATA_EXCLUSION not in claim.limitation_codes
