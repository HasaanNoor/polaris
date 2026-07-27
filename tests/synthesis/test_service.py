import pytest

from polaris.synthesis import SynthesisMode, SynthesisRequest, synthesize_assessment
from polaris.synthesis.errors import SynthesisProviderError
from polaris.synthesis.models import SynthesisFindingCode
from tests.synthesis.helpers import MockProvider, valid_response


def test_mocked_llm_synthesis_uses_provider(coordinated):
    provider = MockProvider(valid_response())
    artifact = synthesize_assessment(
        request=SynthesisRequest(
            coordinated_assessment=coordinated,
            mode=SynthesisMode.LLM,
            model_identifier="mock-model",
        ),
        provider=provider,
    )

    assert provider.calls == 1
    assert artifact.synthesis_mode is SynthesisMode.LLM
    assert artifact.provenance.provider == "mock-provider"
    assert artifact.provenance.model_identifier == "mock-model"
    assert artifact.synthesis_id.startswith("synthesis_run_")


def test_provider_unavailable_falls_back(coordinated):
    artifact = synthesize_assessment(
        request=SynthesisRequest(coordinated_assessment=coordinated, mode=SynthesisMode.LLM)
    )

    assert artifact.synthesis_mode is SynthesisMode.DETERMINISTIC
    assert SynthesisFindingCode.FALLBACK_USED in {
        finding.finding_code for finding in artifact.grounding_findings
    }
    assert artifact.provenance.synthesis_mode_requested is SynthesisMode.LLM


def test_provider_exception_falls_back(coordinated):
    artifact = synthesize_assessment(
        request=SynthesisRequest(coordinated_assessment=coordinated, mode=SynthesisMode.LLM),
        provider=MockProvider(exc=RuntimeError("timeout")),
    )

    assert artifact.synthesis_mode is SynthesisMode.DETERMINISTIC
    assert SynthesisFindingCode.LLM_PROVIDER_UNAVAILABLE in {
        finding.finding_code for finding in artifact.grounding_findings
    }


def test_invalid_response_falls_back(coordinated):
    artifact = synthesize_assessment(
        request=SynthesisRequest(coordinated_assessment=coordinated, mode=SynthesisMode.LLM),
        provider=MockProvider({"overall_summary": "missing fields"}),
    )

    assert artifact.synthesis_mode is SynthesisMode.DETERMINISTIC
    assert SynthesisFindingCode.LLM_RESPONSE_INVALID in {
        finding.finding_code for finding in artifact.grounding_findings
    }


def test_fallback_can_be_disabled(coordinated):
    with pytest.raises(SynthesisProviderError):
        synthesize_assessment(
            request=SynthesisRequest(
                coordinated_assessment=coordinated,
                mode=SynthesisMode.LLM,
                allow_deterministic_fallback=False,
            )
        )
