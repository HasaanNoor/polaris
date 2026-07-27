from polaris.agents.models import AgentDomain, UnsupportedInferenceCode
from polaris.evidence.models import LimitationCode
from polaris.synthesis.models import (
    ProviderCrossDomainSynthesis,
    ProviderDomainSynthesis,
    StructuredSynthesisResponse,
    UncertaintyCode,
)


class MockProvider:
    provider_name = "mock-provider"

    def __init__(self, response=None, *, exc: Exception | None = None):
        self.response = response
        self.exc = exc
        self.calls = 0

    def synthesize(self, *, request, system_prompt, grounding_payload):
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return self.response


def valid_response() -> StructuredSynthesisResponse:
    return StructuredSynthesisResponse(
        overall_summary=(
            "The coordinated assessment indicates association-oriented evidence across "
            "education, economics, and public_health while preserving non-causal boundaries."
        ),
        domain_summaries=(
            ProviderDomainSynthesis(
                domain=AgentDomain.ECONOMICS,
                summary=(
                    "economics selected GDP-related structured references and treats them as "
                    "association evidence only."
                ),
                referenced_claim_ids=("claim_gdp_fertility",),
                referenced_evidence_ids=("evidence_gdp",),
                limitations=(LimitationCode.OBSERVATIONAL_ASSOCIATION,),
            ),
            ProviderDomainSynthesis(
                domain=AgentDomain.EDUCATION,
                summary=(
                    "education selected the literacy-fertility claim as a non-causal "
                    "association reference."
                ),
                referenced_claim_ids=("claim_literacy_fertility",),
                referenced_evidence_ids=("evidence_literacy",),
                limitations=(
                    LimitationCode.LIMITED_MODEL_SCOPE,
                    LimitationCode.MISSING_DATA_EXCLUSION,
                    LimitationCode.OBSERVATIONAL_ASSOCIATION,
                    LimitationCode.UNSUPPORTED_GENERALIZATION,
                ),
            ),
            ProviderDomainSynthesis(
                domain=AgentDomain.PUBLIC_HEALTH,
                summary=(
                    "public_health selected fertility-related structured references without "
                    "making medical conclusions."
                ),
                referenced_claim_ids=("claim_literacy_fertility",),
                referenced_evidence_ids=("evidence_literacy",),
                limitations=(
                    LimitationCode.LIMITED_MODEL_SCOPE,
                    LimitationCode.MISSING_DATA_EXCLUSION,
                    LimitationCode.OBSERVATIONAL_ASSOCIATION,
                    LimitationCode.UNSUPPORTED_GENERALIZATION,
                ),
            ),
            ProviderDomainSynthesis(
                domain=AgentDomain.GOVERNANCE,
                summary="governance was supplied with no relevant evidence in this assessment.",
                referenced_claim_ids=(),
                referenced_evidence_ids=(),
                limitations=(),
            ),
        ),
        cross_domain_findings=(
            ProviderCrossDomainSynthesis(
                summary=(
                    "Claim claim_literacy_fertility appears across education and "
                    "public_health as shared structured relevance, not causal proof."
                ),
                domains=(AgentDomain.EDUCATION, AgentDomain.PUBLIC_HEALTH),
                referenced_claim_ids=("claim_literacy_fertility",),
            ),
        ),
        limitations_summary=(
            "Limitations preserved: LIMITED_MODEL_SCOPE, MISSING_DATA_EXCLUSION, "
            "OBSERVATIONAL_ASSOCIATION, and UNSUPPORTED_GENERALIZATION."
        ),
        evidence_gaps_summary=(
            "Domain gaps include governance having no relevant evidence; evidence strength "
            "is not assessed."
        ),
        unsupported_inferences_preserved=(
            UnsupportedInferenceCode.CAUSALITY,
            UnsupportedInferenceCode.INTERVENTION_RECOMMENDATION,
            UnsupportedInferenceCode.MECHANISM,
            UnsupportedInferenceCode.POLICY_EFFECTIVENESS,
            UnsupportedInferenceCode.POPULATION_WIDE_GENERALIZATION,
            UnsupportedInferenceCode.TEMPORAL_PREDICTION,
            UnsupportedInferenceCode.MEDICAL_CONCLUSION,
        ),
        uncertainty=(
            UncertaintyCode.CAUSAL_INFERENCE_UNSUPPORTED,
            UncertaintyCode.DOMAIN_COVERAGE_INCOMPLETE,
            UncertaintyCode.EVIDENCE_STRENGTH_NOT_ASSESSED,
            UncertaintyCode.GENERALIZATION_LIMITED,
            UncertaintyCode.MODEL_SCOPE_LIMITED,
        ),
        referenced_claim_ids=("claim_gdp_fertility", "claim_literacy_fertility"),
        referenced_evidence_ids=("evidence_gdp", "evidence_literacy"),
    )
