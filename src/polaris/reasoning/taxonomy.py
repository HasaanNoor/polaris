"""Controlled taxonomy for Phase 18 evidence-grounded reasoning."""

from enum import StrEnum


class ReasoningMode(StrEnum):
    DETERMINISTIC = "deterministic"
    PROVIDER_BACKED = "provider_backed"


class ReasoningCategory(StrEnum):
    EMPIRICAL_INTERPRETATION = "empirical_interpretation"
    CROSS_DOMAIN_SYNTHESIS = "cross_domain_synthesis"
    PLAUSIBLE_MECHANISM = "plausible_mechanism"
    ALTERNATIVE_EXPLANATION = "alternative_explanation"
    POTENTIAL_CONFOUNDER = "potential_confounder"
    CONTRADICTION = "contradiction"
    LIMITATION = "limitation"
    UNCERTAINTY = "uncertainty"
    FOLLOW_UP_HYPOTHESIS = "follow_up_hypothesis"
    FOLLOW_UP_RESEARCH_QUESTION = "follow_up_research_question"
    LITERATURE_ALIGNMENT = "literature_alignment"
    LITERATURE_CONTRAST = "literature_contrast"


class EpistemicStatus(StrEnum):
    DIRECTLY_SUPPORTED = "directly_supported"
    SUPPORTED_INTERPRETATION = "supported_interpretation"
    PLAUSIBLE_BUT_UNPROVEN = "plausible_but_unproven"
    SPECULATIVE = "speculative"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class SupportLevel(StrEnum):
    STRONG = "strong"
    MODERATE = "moderate"
    LIMITED = "limited"
    MIXED = "mixed"
    NONE = "none"


class CausalStatus(StrEnum):
    NON_CAUSAL = "non_causal"
    NOT_ESTABLISHED = "not_established"
    CAUSAL_CLAIM_REJECTED = "causal_claim_rejected"
