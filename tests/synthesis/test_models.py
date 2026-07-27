import pytest
from pydantic import ValidationError

from polaris.synthesis import SynthesisMode, SynthesisRequest, synthesize_assessment


def test_synthesis_request_is_frozen_and_rejects_unknown_fields(coordinated):
    request = SynthesisRequest(coordinated_assessment=coordinated)

    with pytest.raises(ValidationError):
        request.mode = SynthesisMode.LLM

    with pytest.raises(ValidationError):
        SynthesisRequest.model_validate(
            {"coordinated_assessment": coordinated.model_dump(), "unexpected": True}
        )


def test_synthesis_request_rejects_mismatched_evidence(coordinated, synthesis_evidence_artifact):
    mismatched = synthesis_evidence_artifact.model_copy(update={"dataset_id": "other"})

    with pytest.raises(ValidationError):
        SynthesisRequest(coordinated_assessment=coordinated, evidence_artifact=mismatched)


def test_deterministic_artifact_serializes_and_has_stable_id(coordinated):
    request = SynthesisRequest(coordinated_assessment=coordinated)
    first = synthesize_assessment(request=request)
    second = synthesize_assessment(request=request)

    assert first.synthesis_id == second.synthesis_id
    assert first.synthesis_mode is SynthesisMode.DETERMINISTIC
    assert first.model_dump_json()
    assert first.source_coordinated_assessment_id == coordinated.coordinated_assessment_id
