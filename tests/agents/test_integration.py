from copy import deepcopy

from polaris.agents.models import AgentDomain, UnsupportedInferenceCode
from polaris.agents.service import run_all_domain_agents
from polaris.evidence.models import LimitationCode

from .helpers import run_integration_artifact


def test_phase3_to_phase6_integration_preserves_lineage_and_limits(tmp_path):
    artifact = run_integration_artifact(tmp_path)
    before = deepcopy(artifact)
    assessments = run_all_domain_agents(evidence_artifact=artifact)

    assert artifact == before
    assert all(
        assessment.source_evidence_artifact_id == artifact.artifact_id for assessment in assessments
    )
    assert all(
        assessment.provenance.source_analysis_result_id == artifact.source_analysis_result_id
        for assessment in assessments
    )
    assert all(
        assessment.provenance.source_checksum_sha256 == artifact.source_checksum_sha256
        for assessment in assessments
    )
    selected_evidence_ids = {
        evidence_id
        for assessment in assessments
        for evidence_id in assessment.relevant_evidence_ids
    }
    selected_claim_ids = {
        claim_id for assessment in assessments for claim_id in assessment.relevant_claim_ids
    }
    assert selected_evidence_ids <= {record.evidence_id for record in artifact.evidence_records}
    assert selected_claim_ids <= {claim.claim_id for claim in artifact.claim_candidates}
    assert any(
        LimitationCode.MISSING_DATA_EXCLUSION in assessment.inherited_limitations
        for assessment in assessments
    )
    assert all(
        UnsupportedInferenceCode.CAUSALITY in assessment.unsupported_inferences
        for assessment in assessments
    )
    education = next(
        assessment for assessment in assessments if assessment.agent_domain is AgentDomain.EDUCATION
    )
    public_health = next(
        assessment
        for assessment in assessments
        if assessment.agent_domain is AgentDomain.PUBLIC_HEALTH
    )
    assert set(education.relevant_claim_ids) & set(public_health.relevant_claim_ids)
