from evidence_helpers import run_fixture_analysis

from polaris.evidence.models import EvidenceArtifact
from polaris.evidence.service import extract_evidence


def test_extract_evidence_returns_artifact_with_traceable_lineage(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="pearson_correlation",
        analysis_type="correlation",
        outcome="y",
        exposures=["x"],
    )

    artifact = extract_evidence(analysis_result=result)

    assert isinstance(artifact, EvidenceArtifact)
    assert artifact.source_analysis_result_id == result.result_id
    assert artifact.dataset_id == result.dataset_id
    assert artifact.source_checksum_sha256 == result.source_checksum_sha256
    assert artifact.provenance.phase4_schema_version == result.schema_version
    assert artifact.provenance.phase5_schema_version == artifact.schema_version
    assert artifact.evidence_records
    assert artifact.claim_candidates
    assert all(
        claim.source_analysis_result_id == result.result_id for claim in artifact.claim_candidates
    )


def test_artifact_serializes_without_invalid_json_or_narrative_text(evidence_ingestion):
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
    payload = artifact.model_dump_json()

    assert "NaN" not in payload
    assert "Infinity" not in payload
    forbidden = ("causes", "leads to", "drives", "produces", "results in", "impacts")
    assert not any(term in payload.lower() for term in forbidden)
    assert all(claim.causal is False for claim in artifact.claim_candidates)


def test_claims_reference_existing_evidence_ids(evidence_ingestion):
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
    evidence_ids = {record.evidence_id for record in artifact.evidence_records}

    assert all(
        set(claim.supporting_evidence_ids) <= evidence_ids for claim in artifact.claim_candidates
    )
