from copy import deepcopy

from polaris.agents.models import AgentDomain, UnsupportedInferenceCode
from polaris.agents.service import run_all_domain_agents
from polaris.coordination import coordinate_assessments
from polaris.evidence.models import LimitationCode
from tests.agents.helpers import run_integration_artifact


def test_phase3_to_phase7_integration_preserves_lineage_and_coordination(tmp_path):
    artifact = run_integration_artifact(tmp_path)
    artifact_before = deepcopy(artifact)
    assessments = run_all_domain_agents(evidence_artifact=artifact)
    assessment_before = tuple(assessment.model_copy(deep=True) for assessment in assessments)
    coordinated = coordinate_assessments(assessments=assessments)
    repeated = coordinate_assessments(assessments=tuple(reversed(assessments)))

    assert artifact == artifact_before
    assert assessments == assessment_before
    assert coordinated.source_checksum_sha256 == artifact.source_checksum_sha256
    assert coordinated.source_analysis_result_id == artifact.source_analysis_result_id
    assert coordinated.source_evidence_artifact_id == artifact.artifact_id
    assert set(coordinated.source_assessment_ids) == {
        assessment.assessment_id for assessment in assessments
    }
    assert coordinated.coordinated_assessment_id == repeated.coordinated_assessment_id
    assert any(record.cross_domain for record in coordinated.claim_domain_map)
    assert any(
        LimitationCode.OBSERVATIONAL_ASSOCIATION is record.limitation_code
        for record in coordinated.shared_limitations
    )
    assert any(
        UnsupportedInferenceCode.CAUSALITY is record.inference_code
        for record in coordinated.shared_unsupported_inferences
    )
    assert AgentDomain.GOVERNANCE in {
        gap.domain for gap in coordinated.domain_gaps if gap.assessment_supplied
    }
    assert "causal=True" not in repr(coordinated)
    assert "narrative" not in coordinated.model_dump_json()
