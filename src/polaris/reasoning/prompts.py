"""Versioned prompt assembly for provider-backed Phase 18 reasoning."""

from polaris.reasoning.models import REASONING_PROMPT_VERSION, ReasoningRequest
from polaris.reasoning.taxonomy import ReasoningCategory

SYSTEM_PROMPT = f"""Polaris Phase 18 evidence-grounded reasoning prompt {REASONING_PROMPT_VERSION}.
Return only the required structured JSON schema.
Reason only from supplied structured artifacts and grounding IDs.
Distinguish empirical findings from interpretation and hypotheses.
Never upgrade association to causation.
Preserve uncertainty and limitations.
Identify contradictions, alternative explanations, candidate confounders, and testable
follow-up questions.
Reference grounding IDs for every substantive statement.
Use literature only as contextual support or contrast, never as empirical validation.
Never fabricate citations, evidence IDs, claim IDs, assessment IDs, or literature evidence IDs.
Never introduce external factual knowledge.
Never produce policy recommendations, medical recommendations, or political advocacy.
Do not include hidden chain-of-thought or private reasoning traces."""


def build_prompt_inputs(request: ReasoningRequest) -> tuple[str, dict[str, object], str]:
    evidence = request.evidence_artifact
    coordinated = request.coordinated_assessment
    literature = request.literature_context
    payload: dict[str, object] = {
        "research_question": request.research_question,
        "allowed_categories": [category.value for category in ReasoningCategory],
        "requested_categories": [category.value for category in request.requested_categories],
        "evidence_artifact_id": evidence.artifact_id,
        "evidence_records": [
            record.model_dump(mode="json") for record in evidence.evidence_records
        ],
        "claim_candidates": [claim.model_dump(mode="json") for claim in evidence.claim_candidates],
        "coordinated_assessment_id": coordinated.coordinated_assessment_id,
        "agent_assessment_ids": list(coordinated.source_assessment_ids),
        "claim_domain_map": [
            record.model_dump(mode="json") for record in coordinated.claim_domain_map
        ],
        "evidence_domain_map": [
            record.model_dump(mode="json") for record in coordinated.evidence_domain_map
        ],
        "agreements": [record.model_dump(mode="json") for record in coordinated.agreements],
        "divergences": [record.model_dump(mode="json") for record in coordinated.divergences],
        "shared_limitations": [
            record.model_dump(mode="json") for record in coordinated.shared_limitations
        ],
        "causal_constraints": [
            "claims are non-causal unless future upstream causal evidence explicitly "
            "says otherwise",
            "mechanisms must be labeled plausible_but_unproven and not_established",
            "do not use causes, drives, improves, worsens, impact of, or effect of as findings",
        ],
    }
    if literature is not None:
        payload["literature_context_id"] = literature.literature_context_id
        payload["literature_evidence"] = [
            record.model_dump(mode="json") for record in literature.literature_evidence
        ]
    user_prompt = (
        "Produce a StructuredReasoningResponse grounded only in the payload. "
        "Every ReasoningStatement must include evidence_ids, claim_ids, "
        "agent_assessment_ids, or literature_evidence_ids."
    )
    return SYSTEM_PROMPT, payload, user_prompt
