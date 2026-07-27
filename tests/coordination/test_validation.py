import pytest

from polaris.agents.models import AgentDomain
from polaris.coordination import coordinate_assessments
from polaris.coordination.errors import (
    AssessmentSourceMismatchError,
    CoordinationValidationError,
    DuplicateAgentDomainError,
)

from .helpers import assessment_for, without_domain


def test_same_evidence_artifact_accepted(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert coordinated.source_evidence_artifact_id == "evidence_artifact_agent"


def test_mismatched_evidence_artifact_rejected(all_assessments):
    bad = all_assessments[0].model_copy(update={"source_evidence_artifact_id": "other"})

    with pytest.raises(AssessmentSourceMismatchError):
        coordinate_assessments(assessments=(bad, *all_assessments[1:]))


def test_mismatched_dataset_rejected(all_assessments):
    bad_provenance = all_assessments[0].provenance.model_copy(update={"dataset_id": "other"})
    bad = all_assessments[0].model_copy(update={"provenance": bad_provenance})

    with pytest.raises(AssessmentSourceMismatchError):
        coordinate_assessments(assessments=(bad, *all_assessments[1:]))


def test_mismatched_checksum_rejected(all_assessments):
    bad_provenance = all_assessments[0].provenance.model_copy(
        update={"source_checksum_sha256": "other"}
    )
    bad = all_assessments[0].model_copy(update={"provenance": bad_provenance})

    with pytest.raises(AssessmentSourceMismatchError):
        coordinate_assessments(assessments=(bad, *all_assessments[1:]))


def test_duplicate_domain_rejected(all_assessments):
    duplicate = assessment_for(all_assessments, AgentDomain.EDUCATION).model_copy(
        update={"assessment_id": "different"}
    )

    with pytest.raises(DuplicateAgentDomainError):
        coordinate_assessments(assessments=(*all_assessments, duplicate))


def test_partial_domain_set_accepted(all_assessments):
    coordinated = coordinate_assessments(
        assessments=without_domain(all_assessments, AgentDomain.GOVERNANCE)
    )

    assert coordinated.missing_domains == (AgentDomain.GOVERNANCE,)


def test_one_agent_accepted(all_assessments):
    coordinated = coordinate_assessments(assessments=(all_assessments[0],))

    assert coordinated.participating_domains == (all_assessments[0].agent_domain,)


def test_invalid_assessment_input_rejected():
    with pytest.raises(CoordinationValidationError):
        coordinate_assessments(assessments=({"not": "assessment"},))
