from evidence_helpers import run_fixture_analysis

from polaris.evidence.models import (
    ClaimType,
    Direction,
    LimitationCode,
    ModelFitEvidenceRecord,
    RegressionCoefficientEvidenceRecord,
)
from polaris.evidence.service import extract_evidence


def test_ols_coefficient_model_fit_and_conditional_claims(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="ordinary_least_squares",
        analysis_type="regression",
        model_family="linear",
        outcome="y",
        exposures=["x"],
        covariates=["z"],
        significance_threshold=0.05,
    )

    artifact = extract_evidence(analysis_result=result)
    coefficients = [
        record
        for record in artifact.evidence_records
        if isinstance(record, RegressionCoefficientEvidenceRecord)
    ]
    intercept = next(record for record in coefficients if record.is_intercept)
    predictor = next(record for record in coefficients if record.variable_id == "x")
    covariate = next(record for record in coefficients if record.variable_id == "z")
    fit = next(
        record for record in artifact.evidence_records if isinstance(record, ModelFitEvidenceRecord)
    )

    assert intercept.term == "intercept"
    assert predictor.estimate is not None
    assert predictor.standard_error is not None
    assert predictor.confidence_interval_low is not None
    assert predictor.below_significance_threshold is not None
    assert covariate.variable_id == "z"
    assert fit.r_squared is not None
    assert fit.sample_size == result.analysis_sample.sample_size

    conditional_claims = [
        claim
        for claim in artifact.claim_candidates
        if claim.claim_type is ClaimType.CONDITIONAL_ASSOCIATION
    ]
    assert len(conditional_claims) == 2
    assert all(claim.causal is False for claim in conditional_claims)
    assert all(
        LimitationCode.OBSERVATIONAL_ASSOCIATION in claim.limitation_codes
        for claim in conditional_claims
    )
    assert all(claim.supporting_evidence_ids for claim in conditional_claims)


def test_singular_design_and_diagnostic_limitations_propagate(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="ordinary_least_squares",
        analysis_type="regression",
        model_family="linear",
        outcome="y",
        exposures=["x", "negative_x"],
    )

    artifact = extract_evidence(analysis_result=result)
    limitation_claims = [
        claim
        for claim in artifact.claim_candidates
        if claim.claim_type is ClaimType.MODEL_LIMITATION
    ]
    conditional_claims = [
        claim
        for claim in artifact.claim_candidates
        if claim.claim_type is ClaimType.CONDITIONAL_ASSOCIATION
    ]

    assert any(
        LimitationCode.MULTICOLLINEARITY in record.limitation_codes
        for record in artifact.evidence_records
    )
    assert limitation_claims
    assert any(
        LimitationCode.MULTICOLLINEARITY in claim.limitation_codes for claim in conditional_claims
    )
    assert all(
        claim.direction in {Direction.POSITIVE, Direction.NEGATIVE, Direction.ZERO}
        for claim in conditional_claims
    )
