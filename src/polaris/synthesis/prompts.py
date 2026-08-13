"""Prompt construction for guardrailed Phase 8 synthesis."""

import json

from polaris.synthesis.grounding import build_grounding_payload
from polaris.synthesis.models import GroundingPayload, SynthesisRequest

SYSTEM_PROMPT = """You are the Polaris Phase 8 synthesis layer.
Use only the supplied structured coordinated assessment payload.
Use supplied literature context only as a separate contextual artifact.
If supplied, use Phase 18 reasoning statements as validated interpretation summaries rather
than redoing unrestricted reasoning from scratch.
Do not use external facts, browsing, retrieval, pretrained contextual facts, or raw data.
Do not calculate statistics or create new numerical evidence.
Do not change upstream claims, limitations, unsupported inference codes, or source IDs.
Do not claim causation, mechanisms as facts, policy effectiveness, interventions,
predictions, or medical conclusions.
Preserve limitations and unsupported-inference boundaries.
Distinguish evidence from cautious interpretation.
Mention meaningful evidence and domain gaps.
Avoid statistical-strength adjectives unless supplied by the payload.
Reference only supplied claim IDs, evidence IDs, agreement IDs, divergence IDs, assessment IDs,
literature evidence IDs, and literature chunk IDs.
Never fabricate IDs or numerical values.
Return only a structured response matching the requested schema."""


def build_prompt_inputs(request: SynthesisRequest) -> tuple[str, GroundingPayload, str]:
    payload = build_grounding_payload(
        request.coordinated_assessment,
        evidence_artifact=request.evidence_artifact,
        literature_context=request.literature_context,
        reasoning_artifact=request.reasoning_artifact,
    )
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    user_prompt = (
        "Create a concise interdisciplinary synthesis from this JSON grounding payload. "
        "Every substantive domain or cross-domain statement must cite supplied IDs.\n\n"
        f"{payload_json}"
    )
    return SYSTEM_PROMPT, payload, user_prompt
