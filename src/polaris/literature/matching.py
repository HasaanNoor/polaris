"""Deterministic empirical-claim to literature matching."""

from collections.abc import Mapping

from polaris.evidence.models import ClaimCandidate, ClaimType, Direction, EvidenceArtifact
from polaris.literature.models import ClaimLiteratureQuery
from polaris.schemas.research_question import ResearchQuestion

_METHOD_TERMS = {
    "pearson_correlation": ("correlation", "association"),
    "spearman_correlation": ("correlation", "association"),
    "ordinary_least_squares": ("regression", "association"),
    "descriptive_statistics": ("descriptive",),
}
_DIRECTION_TERMS = {
    Direction.POSITIVE: ("positive",),
    Direction.NEGATIVE: ("negative",),
    Direction.ZERO: ("no association",),
}


def build_claim_literature_queries(
    *,
    evidence_artifact: EvidenceArtifact,
    research_question: ResearchQuestion | None = None,
    variable_labels: Mapping[str, str] | None = None,
) -> tuple[ClaimLiteratureQuery, ...]:
    labels = variable_labels or {}
    return tuple(
        build_claim_literature_query(
            claim=claim,
            research_question=research_question,
            variable_labels=labels,
        )
        for claim in evidence_artifact.claim_candidates
    )


def build_claim_literature_query(
    *,
    claim: ClaimCandidate,
    research_question: ResearchQuestion | None = None,
    variable_labels: Mapping[str, str] | None = None,
) -> ClaimLiteratureQuery:
    labels = variable_labels or {}
    variable_ids = tuple(
        item
        for item in (claim.subject_variable, claim.outcome_variable, *claim.related_variables)
        if item is not None
    )
    variable_terms = tuple(
        dict.fromkeys(
            _clean_label(labels.get(variable_id, variable_id)) for variable_id in variable_ids
        )
    )
    method_terms = _METHOD_TERMS.get(claim.statistical_procedure.value, (claim.claim_type.value,))
    if claim.claim_type in {ClaimType.ASSOCIATION, ClaimType.CONDITIONAL_ASSOCIATION}:
        method_terms = tuple(dict.fromkeys((*method_terms, "cross-country association")))
    direction_terms = _DIRECTION_TERMS.get(claim.direction, ())
    question_terms = ()
    if research_question is not None:
        question_terms = tuple(
            _clean_label(ref.variable_id)
            for ref in (
                *research_question.outcome_variables,
                *research_question.exposure_variables,
                *research_question.covariates,
            )
        )
    terms = tuple(
        item
        for item in (
            *variable_terms,
            *question_terms,
            *method_terms,
            *direction_terms,
        )
        if item
    )
    query = " ".join(dict.fromkeys(terms))
    return ClaimLiteratureQuery(
        empirical_claim_id=claim.claim_id,
        query=query or claim.claim_type.value,
        variable_terms=variable_terms,
        method_terms=tuple(method_terms),
        domain_terms=question_terms,
    )


def _clean_label(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().lower()
