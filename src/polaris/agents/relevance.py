"""Deterministic domain relevance rules for Phase 6 agents."""

import re
from collections.abc import Iterable

from polaris.agents.models import (
    AgentDomain,
    ConceptCategory,
    DomainRelevanceRecord,
    RelevanceReasonCode,
    RelevanceSourceType,
    RelevanceStatus,
)
from polaris.evidence.models import (
    AnalysisWarningEvidenceRecord,
    ClaimCandidate,
    CorrelationEvidenceRecord,
    DescriptiveEvidenceRecord,
    DiagnosticEvidenceRecord,
    EvidenceRecord,
    ModelFitEvidenceRecord,
    RegressionCoefficientEvidenceRecord,
    SampleQualityEvidenceRecord,
)

DOMAIN_CONCEPTS: dict[AgentDomain, frozenset[ConceptCategory]] = {
    AgentDomain.GOVERNANCE: frozenset(
        {
            ConceptCategory.GOVERNANCE,
            ConceptCategory.INSTITUTIONS,
            ConceptCategory.RULE_OF_LAW,
            ConceptCategory.CORRUPTION,
            ConceptCategory.GOVERNMENT_EFFECTIVENESS,
            ConceptCategory.POLITICAL_STABILITY,
            ConceptCategory.PUBLIC_SERVICES,
            ConceptCategory.CIVIC_PARTICIPATION,
            ConceptCategory.STATE_CAPACITY,
        }
    ),
    AgentDomain.ECONOMICS: frozenset(
        {
            ConceptCategory.GDP,
            ConceptCategory.INCOME,
            ConceptCategory.EMPLOYMENT,
            ConceptCategory.LABOR_FORCE,
            ConceptCategory.PRODUCTIVITY,
            ConceptCategory.POVERTY,
            ConceptCategory.INEQUALITY,
            ConceptCategory.TRADE,
            ConceptCategory.INFLATION,
            ConceptCategory.ECONOMIC_GROWTH,
        }
    ),
    AgentDomain.EDUCATION: frozenset(
        {
            ConceptCategory.LITERACY,
            ConceptCategory.SCHOOL_ENROLLMENT,
            ConceptCategory.EDUCATIONAL_ATTAINMENT,
            ConceptCategory.YEARS_OF_SCHOOLING,
            ConceptCategory.COMPLETION,
            ConceptCategory.EDUCATION_ACCESS,
            ConceptCategory.LEARNING_OUTCOMES,
        }
    ),
    AgentDomain.PUBLIC_HEALTH: frozenset(
        {
            ConceptCategory.LIFE_EXPECTANCY,
            ConceptCategory.MORTALITY,
            ConceptCategory.MATERNAL_HEALTH,
            ConceptCategory.INFANT_MORTALITY,
            ConceptCategory.DISEASE,
            ConceptCategory.HEALTHCARE_ACCESS,
            ConceptCategory.NUTRITION,
            ConceptCategory.FERTILITY,
            ConceptCategory.HEALTH_EXPENDITURE,
        }
    ),
}

VARIABLE_CONCEPT_MAPPINGS: dict[str, tuple[ConceptCategory, ...]] = {
    "civic_participation": (ConceptCategory.CIVIC_PARTICIPATION,),
    "control_of_corruption": (ConceptCategory.CORRUPTION,),
    "corruption_index": (ConceptCategory.CORRUPTION,),
    "government_effectiveness": (ConceptCategory.GOVERNMENT_EFFECTIVENESS,),
    "governance_index": (ConceptCategory.GOVERNANCE,),
    "institutional_quality": (ConceptCategory.INSTITUTIONS,),
    "political_stability": (ConceptCategory.POLITICAL_STABILITY,),
    "public_service_delivery": (ConceptCategory.PUBLIC_SERVICES,),
    "rule_of_law": (ConceptCategory.RULE_OF_LAW,),
    "state_capacity": (ConceptCategory.STATE_CAPACITY,),
    "employment_rate": (ConceptCategory.EMPLOYMENT,),
    "gdp": (ConceptCategory.GDP,),
    "gdp_per_capita": (ConceptCategory.GDP,),
    "income": (ConceptCategory.INCOME,),
    "income_per_capita": (ConceptCategory.INCOME,),
    "inequality_index": (ConceptCategory.INEQUALITY,),
    "inflation_rate": (ConceptCategory.INFLATION,),
    "labor_force_participation": (ConceptCategory.LABOR_FORCE,),
    "poverty_rate": (ConceptCategory.POVERTY,),
    "productivity": (ConceptCategory.PRODUCTIVITY,),
    "trade_share": (ConceptCategory.TRADE,),
    "economic_growth": (ConceptCategory.ECONOMIC_GROWTH,),
    "completion_rate": (ConceptCategory.COMPLETION,),
    "education_access": (ConceptCategory.EDUCATION_ACCESS,),
    "educational_attainment": (ConceptCategory.EDUCATIONAL_ATTAINMENT,),
    "enrollment_rate": (ConceptCategory.SCHOOL_ENROLLMENT,),
    "female_literacy": (ConceptCategory.LITERACY,),
    "learning_outcomes": (ConceptCategory.LEARNING_OUTCOMES,),
    "literacy_rate": (ConceptCategory.LITERACY,),
    "school_enrollment": (ConceptCategory.SCHOOL_ENROLLMENT,),
    "years_of_schooling": (ConceptCategory.YEARS_OF_SCHOOLING,),
    "disease_burden": (ConceptCategory.DISEASE,),
    "fertility": (ConceptCategory.FERTILITY,),
    "fertility_rate": (ConceptCategory.FERTILITY,),
    "health_expenditure": (ConceptCategory.HEALTH_EXPENDITURE,),
    "healthcare_access": (ConceptCategory.HEALTHCARE_ACCESS,),
    "infant_mortality": (ConceptCategory.INFANT_MORTALITY,),
    "life_expectancy": (ConceptCategory.LIFE_EXPECTANCY,),
    "maternal_mortality": (ConceptCategory.MATERNAL_HEALTH, ConceptCategory.MORTALITY),
    "mortality_rate": (ConceptCategory.MORTALITY,),
    "nutrition_index": (ConceptCategory.NUTRITION,),
}

KEYWORD_CONCEPT_MAPPINGS: dict[str, ConceptCategory] = {
    "civic": ConceptCategory.CIVIC_PARTICIPATION,
    "corruption": ConceptCategory.CORRUPTION,
    "governance": ConceptCategory.GOVERNANCE,
    "government": ConceptCategory.GOVERNMENT_EFFECTIVENESS,
    "institution": ConceptCategory.INSTITUTIONS,
    "law": ConceptCategory.RULE_OF_LAW,
    "political": ConceptCategory.POLITICAL_STABILITY,
    "state": ConceptCategory.STATE_CAPACITY,
    "gdp": ConceptCategory.GDP,
    "income": ConceptCategory.INCOME,
    "employment": ConceptCategory.EMPLOYMENT,
    "labor": ConceptCategory.LABOR_FORCE,
    "poverty": ConceptCategory.POVERTY,
    "productivity": ConceptCategory.PRODUCTIVITY,
    "trade": ConceptCategory.TRADE,
    "inflation": ConceptCategory.INFLATION,
    "literacy": ConceptCategory.LITERACY,
    "enrollment": ConceptCategory.SCHOOL_ENROLLMENT,
    "attainment": ConceptCategory.EDUCATIONAL_ATTAINMENT,
    "schooling": ConceptCategory.YEARS_OF_SCHOOLING,
    "completion": ConceptCategory.COMPLETION,
    "education": ConceptCategory.EDUCATION_ACCESS,
    "learning": ConceptCategory.LEARNING_OUTCOMES,
    "fertility": ConceptCategory.FERTILITY,
    "mortality": ConceptCategory.MORTALITY,
    "expectancy": ConceptCategory.LIFE_EXPECTANCY,
    "maternal": ConceptCategory.MATERNAL_HEALTH,
    "infant": ConceptCategory.INFANT_MORTALITY,
    "disease": ConceptCategory.DISEASE,
    "healthcare": ConceptCategory.HEALTHCARE_ACCESS,
    "nutrition": ConceptCategory.NUTRITION,
    "health": ConceptCategory.HEALTHCARE_ACCESS,
}


def classify_variable(variable_id: str) -> tuple[ConceptCategory, ...]:
    normalized = _normalize_variable_id(variable_id)
    concepts = list(VARIABLE_CONCEPT_MAPPINGS.get(normalized, ()))
    if concepts:
        return tuple(sorted(set(concepts), key=lambda item: item.value))

    tokens = set(_variable_tokens(normalized))
    keyword_concepts = [
        concept for keyword, concept in KEYWORD_CONCEPT_MAPPINGS.items() if keyword in tokens
    ]
    return tuple(sorted(set(keyword_concepts), key=lambda item: item.value))


def relevance_for_evidence(domain: AgentDomain, evidence: EvidenceRecord) -> DomainRelevanceRecord:
    variable_ids = _evidence_variable_ids(evidence)
    return _build_relevance_record(
        domain=domain,
        source_id=evidence.evidence_id,
        source_type=RelevanceSourceType.EVIDENCE_RECORD,
        variable_ids=variable_ids,
        supporting_evidence_ids=(),
        all_evidence_by_id={},
        context="evidence",
    )


def relevance_for_claim(
    domain: AgentDomain,
    claim: ClaimCandidate,
    evidence_by_id: dict[str, EvidenceRecord],
) -> DomainRelevanceRecord:
    variable_ids = _claim_variable_ids(claim)
    return _build_relevance_record(
        domain=domain,
        source_id=claim.claim_id,
        source_type=RelevanceSourceType.CLAIM_CANDIDATE,
        variable_ids=variable_ids,
        supporting_evidence_ids=claim.supporting_evidence_ids,
        all_evidence_by_id=evidence_by_id,
        context="claim",
    )


def _build_relevance_record(
    *,
    domain: AgentDomain,
    source_id: str,
    source_type: RelevanceSourceType,
    variable_ids: tuple[str, ...],
    supporting_evidence_ids: tuple[str, ...],
    all_evidence_by_id: dict[str, EvidenceRecord],
    context: str,
) -> DomainRelevanceRecord:
    concepts_by_variable = {
        variable_id: classify_variable(variable_id) for variable_id in variable_ids
    }
    matched = _matched_domain_variables(domain, concepts_by_variable)
    reasons: list[RelevanceReasonCode] = []
    status = RelevanceStatus.NOT_RELEVANT
    matched_concepts = tuple(
        concept
        for variable_id in matched
        for concept in concepts_by_variable[variable_id]
        if concept in DOMAIN_CONCEPTS[domain]
    )

    if matched:
        status = RelevanceStatus.RELEVANT
        reasons.append(RelevanceReasonCode.DIRECT_DOMAIN_VARIABLE)
        if _has_keyword_only_match(matched):
            reasons.append(RelevanceReasonCode.KEYWORD_VARIABLE_MATCH)

    if context == "claim":
        support_domain_vars = _supporting_domain_variables(
            domain, supporting_evidence_ids, all_evidence_by_id
        )
        if support_domain_vars:
            matched = tuple(sorted(set((*matched, *support_domain_vars))))
            matched_concepts = tuple(
                sorted(
                    set((*matched_concepts, *(_concepts_for_variables(support_domain_vars)))),
                    key=lambda item: item.value,
                )
            )
            reasons.append(RelevanceReasonCode.DOMAIN_CONTROL_PRESENT)
            status = RelevanceStatus.RELEVANT

        if matched and _claim_spans_domains(variable_ids):
            reasons.append(RelevanceReasonCode.CROSS_DOMAIN_RELATIONSHIP)

    if context == "evidence" and not matched and _is_context_evidence(evidence_id=source_id):
        reasons.append(RelevanceReasonCode.NO_DOMAIN_MATCH)

    if not reasons:
        reasons.append(RelevanceReasonCode.NO_DOMAIN_MATCH)

    return DomainRelevanceRecord(
        source_id=source_id,
        source_type=source_type,
        agent_domain=domain,
        relevance_status=status,
        relevance_reason_codes=tuple(reasons),
        matched_variable_ids=matched,
        matched_concept_categories=matched_concepts,
    )


def _matched_domain_variables(
    domain: AgentDomain,
    concepts_by_variable: dict[str, tuple[ConceptCategory, ...]],
) -> tuple[str, ...]:
    domain_concepts = DOMAIN_CONCEPTS[domain]
    return tuple(
        sorted(
            variable_id
            for variable_id, concepts in concepts_by_variable.items()
            if any(concept in domain_concepts for concept in concepts)
        )
    )


def _supporting_domain_variables(
    domain: AgentDomain,
    supporting_evidence_ids: Iterable[str],
    evidence_by_id: dict[str, EvidenceRecord],
) -> tuple[str, ...]:
    values: list[str] = []
    for evidence_id in supporting_evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            continue
        variables = _evidence_variable_ids(evidence)
        concepts_by_variable = {
            variable_id: classify_variable(variable_id) for variable_id in variables
        }
        values.extend(_matched_domain_variables(domain, concepts_by_variable))
    return tuple(sorted(set(values)))


def _concepts_for_variables(variable_ids: Iterable[str]) -> tuple[ConceptCategory, ...]:
    return tuple(
        sorted(
            {concept for variable_id in variable_ids for concept in classify_variable(variable_id)},
            key=lambda item: item.value,
        )
    )


def _claim_spans_domains(variable_ids: tuple[str, ...]) -> bool:
    domains = {
        domain
        for variable_id in variable_ids
        for concept in classify_variable(variable_id)
        for domain, domain_concepts in DOMAIN_CONCEPTS.items()
        if concept in domain_concepts
    }
    return len(domains) > 1


def _has_keyword_only_match(variable_ids: Iterable[str]) -> bool:
    return any(
        _normalize_variable_id(variable_id) not in VARIABLE_CONCEPT_MAPPINGS
        and classify_variable(variable_id)
        for variable_id in variable_ids
    )


def _evidence_variable_ids(evidence: EvidenceRecord) -> tuple[str, ...]:
    if isinstance(evidence, DescriptiveEvidenceRecord):
        return (evidence.variable_id,)
    if isinstance(evidence, CorrelationEvidenceRecord):
        return tuple(sorted({evidence.variable_id_1, evidence.variable_id_2}))
    if isinstance(evidence, RegressionCoefficientEvidenceRecord):
        values = [evidence.dependent_variable_id, *evidence.predictor_variable_ids]
        if evidence.variable_id is not None:
            values.append(evidence.variable_id)
        return tuple(sorted(set(values)))
    if isinstance(evidence, ModelFitEvidenceRecord):
        return tuple(sorted({evidence.dependent_variable_id, *evidence.predictor_variable_ids}))
    if isinstance(evidence, DiagnosticEvidenceRecord):
        return () if evidence.variable_id is None else (evidence.variable_id,)
    if isinstance(evidence, SampleQualityEvidenceRecord):
        return tuple(sorted(set(evidence.required_variable_ids)))
    if isinstance(evidence, AnalysisWarningEvidenceRecord):
        return tuple(sorted(set(evidence.variable_ids)))
    return ()


def _claim_variable_ids(claim: ClaimCandidate) -> tuple[str, ...]:
    values = [*claim.related_variables]
    if claim.subject_variable is not None:
        values.append(claim.subject_variable)
    if claim.outcome_variable is not None:
        values.append(claim.outcome_variable)
    return tuple(sorted(set(values)))


def _normalize_variable_id(variable_id: str) -> str:
    return variable_id.strip().lower().replace("-", "_").replace(" ", "_")


def _variable_tokens(variable_id: str) -> tuple[str, ...]:
    return tuple(token for token in re.split(r"[_\W]+", variable_id) if token)


def _is_context_evidence(*, evidence_id: str) -> bool:
    return evidence_id != ""
