from polaris.synthesis import SynthesisRequest
from polaris.synthesis.prompts import build_prompt_inputs


def test_prompt_payload_contains_structured_grounding(coordinated, synthesis_evidence_artifact):
    request = SynthesisRequest(
        coordinated_assessment=coordinated,
        evidence_artifact=synthesis_evidence_artifact,
    )

    system_prompt, payload, user_prompt = build_prompt_inputs(request)

    assert "Do not use external facts" in system_prompt
    assert "claim_literacy_fertility" in user_prompt
    assert "evidence_literacy" in user_prompt
    assert "OBSERVATIONAL_ASSOCIATION" in user_prompt
    assert "unsupported_inferences" in payload
    assert "domain_gaps" in payload
    assert "female_literacy" in user_prompt
    assert "country,fertility_rate" not in user_prompt


def test_prompt_payload_ordering_is_deterministic(coordinated, synthesis_evidence_artifact):
    request = SynthesisRequest(
        coordinated_assessment=coordinated,
        evidence_artifact=synthesis_evidence_artifact,
    )

    assert build_prompt_inputs(request)[2] == build_prompt_inputs(request)[2]
