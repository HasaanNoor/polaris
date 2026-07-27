from copy import deepcopy

from polaris.agents.models import UnsupportedInferenceCode
from polaris.agents.service import run_all_domain_agents
from polaris.coordination import coordinate_assessments
from polaris.evidence.models import LimitationCode
from polaris.synthesis import SynthesisRequest, synthesize_assessment
from tests.agents.helpers import run_integration_artifact


def test_phase3_to_phase8_deterministic_integration_preserves_lineage(tmp_path):
    evidence_artifact = run_integration_artifact(tmp_path)
    before = deepcopy(evidence_artifact)
    assessments = run_all_domain_agents(evidence_artifact=evidence_artifact)
    coordinated = coordinate_assessments(assessments=assessments)
    coordinated_before = coordinated.model_copy(deep=True)

    synthesis = synthesize_assessment(
        request=SynthesisRequest(
            coordinated_assessment=coordinated,
            evidence_artifact=evidence_artifact,
        )
    )

    assert evidence_artifact == before
    assert coordinated == coordinated_before
    assert synthesis.provenance.source_checksum_sha256 == evidence_artifact.source_checksum_sha256
    assert synthesis.provenance.source_evidence_artifact_id == evidence_artifact.artifact_id
    assert (
        synthesis.provenance.source_analysis_result_id
        == evidence_artifact.source_analysis_result_id
    )
    assert synthesis.source_coordinated_assessment_id == coordinated.coordinated_assessment_id
    assert set(synthesis.referenced_claim_ids) <= {
        claim.claim_id for claim in evidence_artifact.claim_candidates
    }
    assert set(synthesis.referenced_evidence_ids) <= {
        record.evidence_id for record in evidence_artifact.evidence_records
    }
    assert UnsupportedInferenceCode.CAUSALITY in synthesis.unsupported_inferences_preserved
    assert "OBSERVATIONAL_ASSOCIATION" in synthesis.limitations_summary
    assert LimitationCode.OBSERVATIONAL_ASSOCIATION in {
        limitation for summary in synthesis.domain_summaries for limitation in summary.limitations
    }
