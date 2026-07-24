import math

import pytest
from pydantic import ValidationError

from polaris.evidence.models import (
    EVIDENCE_SCHEMA_VERSION,
    ClaimCandidate,
    ClaimType,
    CorrelationEvidenceRecord,
    Direction,
    EvidenceProvenance,
    LimitationCode,
)


def test_valid_evidence_record_is_immutable():
    record = CorrelationEvidenceRecord(
        evidence_id="evidence_test",
        source_analysis_result_id="analysis_test",
        dataset_id="dataset",
        source_checksum_sha256="abc",
        statistical_procedure="pearson_correlation",
        sample_size=3,
        provenance=_provenance(),
        variable_id_1="x",
        variable_id_2="y",
        method="pearson",
        correlation_coefficient=1.0,
        p_value=0.0,
        observation_count=3,
        defined=True,
        direction=Direction.POSITIVE,
        missing_exclusion_count=0,
    )

    with pytest.raises(ValidationError):
        record.sample_size = 4


def test_evidence_rejects_unknown_type_unknown_field_and_nan():
    payload = {
        "evidence_id": "evidence_test",
        "evidence_type": "correlation",
        "source_analysis_result_id": "analysis_test",
        "dataset_id": "dataset",
        "source_checksum_sha256": "abc",
        "statistical_procedure": "pearson_correlation",
        "sample_size": 3,
        "provenance": _provenance(),
        "variable_id_1": "x",
        "variable_id_2": "y",
        "method": "pearson",
        "correlation_coefficient": math.nan,
        "observation_count": 3,
        "defined": True,
        "direction": "positive",
        "missing_exclusion_count": 0,
        "extra": True,
    }
    with pytest.raises(ValidationError):
        CorrelationEvidenceRecord.model_validate(payload)


def test_claim_requires_support_and_rejects_causal_true():
    with pytest.raises(ValidationError):
        ClaimCandidate(
            claim_id="claim_bad",
            claim_type=ClaimType.ASSOCIATION,
            statistical_procedure="pearson_correlation",
            supporting_evidence_ids=(),
            causal=False,
            source_analysis_result_id="analysis_test",
            dataset_id="dataset",
            provenance=_provenance(),
        )
    with pytest.raises(ValidationError):
        ClaimCandidate.model_validate(
            {
                "claim_id": "claim_bad",
                "claim_type": "association",
                "statistical_procedure": "pearson_correlation",
                "supporting_evidence_ids": ("evidence_test",),
                "causal": True,
                "source_analysis_result_id": "analysis_test",
                "dataset_id": "dataset",
                "provenance": _provenance(),
            }
        )


def test_claim_sorts_limitations_and_support_ids():
    claim = ClaimCandidate(
        claim_id="claim_test",
        claim_type=ClaimType.ASSOCIATION,
        statistical_procedure="pearson_correlation",
        supporting_evidence_ids=("evidence_b", "evidence_a", "evidence_a"),
        limitation_codes=(
            LimitationCode.UNSUPPORTED_GENERALIZATION,
            LimitationCode.OBSERVATIONAL_ASSOCIATION,
        ),
        causal=False,
        source_analysis_result_id="analysis_test",
        dataset_id="dataset",
        provenance=_provenance(),
    )

    assert claim.supporting_evidence_ids == ("evidence_a", "evidence_b")
    assert claim.causal is False
    assert "NaN" not in claim.model_dump_json()


def _provenance():
    return EvidenceProvenance(
        dataset_id="dataset",
        source_checksum_sha256="abc",
        source_analysis_result_id="analysis_test",
        statistical_procedure="pearson_correlation",
        phase4_schema_version="1.0.0",
        phase5_schema_version=EVIDENCE_SCHEMA_VERSION,
        extraction_timestamp="2026-07-24T00:00:00Z",
        software_version="polaris-test",
    )
