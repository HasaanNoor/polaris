import pytest

from polaris.agents.models import AgentDomain
from polaris.evidence.models import LimitationCode
from polaris.synthesis.errors import GroundingValidationError
from polaris.synthesis.models import (
    ProviderDomainSynthesis,
    StructuredSynthesisResponse,
)
from polaris.synthesis.validation import validate_provider_response, validate_text_grounding
from tests.synthesis.helpers import valid_response


def test_valid_structured_response_passes(coordinated):
    findings = validate_provider_response(valid_response(), coordinated)

    assert all(finding.finding_code.value != "FABRICATED_REFERENCE" for finding in findings)


def test_fabricated_claim_id_rejected(coordinated):
    response = valid_response().model_copy(update={"referenced_claim_ids": ("claim_fake",)})

    with pytest.raises(GroundingValidationError):
        validate_provider_response(response, coordinated)


def test_fabricated_evidence_id_rejected(coordinated):
    response = valid_response().model_copy(update={"referenced_evidence_ids": ("evidence_fake",)})

    with pytest.raises(GroundingValidationError):
        validate_provider_response(response, coordinated)


def test_missing_domain_cannot_have_evidence_references(coordinated):
    response = valid_response().model_copy(
        update={
            "domain_summaries": (
                ProviderDomainSynthesis(
                    domain=AgentDomain.GOVERNANCE,
                    summary="governance produced evidence.",
                    referenced_evidence_ids=("evidence_literacy",),
                    limitations=(),
                ),
            )
        }
    )

    with pytest.raises(GroundingValidationError):
        validate_provider_response(response, coordinated)


def test_omitted_required_limitation_rejected(coordinated):
    response = StructuredSynthesisResponse(
        **{
            **valid_response().model_dump(),
            "limitations_summary": "Only limited evidence is available.",
            "domain_summaries": (
                ProviderDomainSynthesis(
                    domain=AgentDomain.EDUCATION,
                    summary="education selected association evidence.",
                    referenced_claim_ids=("claim_literacy_fertility",),
                    referenced_evidence_ids=("evidence_literacy",),
                    limitations=(LimitationCode.OBSERVATIONAL_ASSOCIATION,),
                ),
            ),
        }
    )

    with pytest.raises(GroundingValidationError):
        validate_provider_response(response, coordinated)


def test_causal_language_guard_context():
    assert not validate_text_grounding(("causal inference is unsupported.",))
    assert not validate_text_grounding(("X is associated with Y.",))
    assert validate_text_grounding(("X causes Y.",))
    assert validate_text_grounding(("X leads to Y.",))
    assert validate_text_grounding(("governments must implement the policy.",))
    assert validate_text_grounding(("patients should receive treatment.",))
