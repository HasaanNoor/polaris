"""Deterministic fallback reasoning for Phase 18."""

from collections import defaultdict
from datetime import UTC, datetime

from polaris.agents.models import AgentDomain
from polaris.evidence.models import (
    ClaimCandidate,
    ClaimType,
    Direction,
    EvidenceArtifact,
    EvidenceType,
    LimitationCode,
    RegressionCoefficientEvidenceRecord,
)
from polaris.evidence.provenance import deterministic_id
from polaris.literature.models import (
    LiteratureSupportClassification,
)
from polaris.reasoning.models import (
    REASONING_RULESET_VERSION,
    REASONING_SCHEMA_VERSION,
    CandidateConfounder,
    ContradictionRecord,
    GroundingSummary,
    ReasoningArtifact,
    ReasoningProvenance,
    ReasoningRequest,
    ReasoningStatement,
)
from polaris.reasoning.taxonomy import (
    CausalStatus,
    EpistemicStatus,
    ReasoningCategory,
    ReasoningMode,
    SupportLevel,
)


def deterministic_reasoning_artifact(
    request: ReasoningRequest,
    *,
    reasoning_timestamp: datetime | None = None,
    deterministic_fallback_used: bool = False,
    rejected_provider_statements: int = 0,
    unsupported_grounding_attempts: int = 0,
    causal_guard_violations: int = 0,
) -> ReasoningArtifact:
    """Create conservative structured reasoning without provider access."""

    statements = _statements(request)
    if request.max_statement_count is not None:
        statements = statements[: request.max_statement_count]
    contradictions = _contradictions(request)
    confounders = _candidate_confounders(request)
    follow_up_hypotheses = tuple(
        item for item in statements if item.category is ReasoningCategory.FOLLOW_UP_HYPOTHESIS
    )
    follow_up_questions = tuple(
        item
        for item in statements
        if item.category is ReasoningCategory.FOLLOW_UP_RESEARCH_QUESTION
    )
    limitations = tuple(
        item for item in statements if item.category is ReasoningCategory.LIMITATION
    )
    grounding_summary = _grounding_summary(
        statements=tuple(statements),
        contradictions=contradictions,
        confounders=confounders,
        rejected_provider_statements=rejected_provider_statements,
        unsupported_grounding_attempts=unsupported_grounding_attempts,
        causal_guard_violations=causal_guard_violations,
    )
    content_payload = {
        "research_question": request.research_question,
        "mode": ReasoningMode.DETERMINISTIC.value,
        "statements": [item.model_dump(mode="json") for item in statements],
        "contradictions": [item.model_dump(mode="json") for item in contradictions],
        "candidate_confounders": [item.model_dump(mode="json") for item in confounders],
        "grounding_summary": grounding_summary.model_dump(mode="json"),
        "ruleset_version": REASONING_RULESET_VERSION,
        "schema_version": REASONING_SCHEMA_VERSION,
    }
    content_digest = deterministic_id("sha256_", content_payload).removeprefix("sha256_")
    reasoning_id = deterministic_id(
        "reasoning_",
        {
            "research_question": request.research_question,
            "source_evidence_artifact_id": request.evidence_artifact.artifact_id,
            "source_coordinated_assessment_id": (
                request.coordinated_assessment.coordinated_assessment_id
            ),
            "literature_context_id": (
                request.literature_context.literature_context_id
                if request.literature_context is not None
                else None
            ),
            "mode": ReasoningMode.DETERMINISTIC.value,
            "content_digest_sha256": content_digest,
            "ruleset_version": REASONING_RULESET_VERSION,
            "schema_version": REASONING_SCHEMA_VERSION,
        },
    )
    timestamp = reasoning_timestamp or datetime.now(UTC)
    provenance = ReasoningProvenance(
        source_evidence_artifact_id=request.evidence_artifact.artifact_id,
        source_coordinated_assessment_id=(request.coordinated_assessment.coordinated_assessment_id),
        source_analysis_result_id=request.evidence_artifact.source_analysis_result_id,
        dataset_id=request.evidence_artifact.dataset_id,
        source_checksum_sha256=request.evidence_artifact.source_checksum_sha256,
        source_assessment_ids=request.coordinated_assessment.source_assessment_ids,
        literature_context_id=(
            request.literature_context.literature_context_id
            if request.literature_context is not None
            else None
        ),
        reasoning_mode_requested=request.mode,
        reasoning_mode_used=ReasoningMode.DETERMINISTIC,
        content_digest_sha256=content_digest,
        reasoning_timestamp=timestamp,
        software_version=request.evidence_artifact.software_version,
        phase5_schema_version=request.evidence_artifact.schema_version,
        phase7_schema_version=request.coordinated_assessment.schema_version,
        phase14_schema_version=(
            request.literature_context.schema_version
            if request.literature_context is not None
            else None
        ),
    )
    return ReasoningArtifact(
        reasoning_id=reasoning_id,
        research_question=request.research_question,
        mode=ReasoningMode.DETERMINISTIC,
        evidence_artifact_id=request.evidence_artifact.artifact_id,
        coordinated_assessment_id=request.coordinated_assessment.coordinated_assessment_id,
        literature_context_id=(
            request.literature_context.literature_context_id
            if request.literature_context is not None
            else None
        ),
        reasoning_statements=tuple(statements),
        contradictions=contradictions,
        candidate_confounders=confounders,
        follow_up_hypotheses=follow_up_hypotheses,
        follow_up_research_questions=follow_up_questions,
        limitations=limitations,
        grounding_summary=grounding_summary,
        deterministic_fallback_used=deterministic_fallback_used,
        provenance=provenance,
        creation_timestamp=timestamp,
    )


def _statements(request: ReasoningRequest) -> list[ReasoningStatement]:
    categories = set(request.requested_categories)
    statements: list[ReasoningStatement] = []
    claims = sorted(request.evidence_artifact.claim_candidates, key=lambda item: item.claim_id)
    for claim in claims:
        if (
            claim.claim_type in {ClaimType.ASSOCIATION, ClaimType.CONDITIONAL_ASSOCIATION}
            and ReasoningCategory.EMPIRICAL_INTERPRETATION in categories
        ):
            statements.append(_empirical_interpretation(claim, request))
    if ReasoningCategory.CROSS_DOMAIN_SYNTHESIS in categories:
        statements.extend(_cross_domain_statements(request))
    if ReasoningCategory.PLAUSIBLE_MECHANISM in categories:
        statements.extend(_mechanism_statements(request))
    if ReasoningCategory.ALTERNATIVE_EXPLANATION in categories:
        statements.extend(_alternative_explanations(request))
    if ReasoningCategory.POTENTIAL_CONFOUNDER in categories:
        statements.extend(_confounder_statements(request))
    if ReasoningCategory.LIMITATION in categories:
        statements.extend(_limitation_statements(request))
    if ReasoningCategory.FOLLOW_UP_HYPOTHESIS in categories:
        statements.extend(_follow_up_hypotheses(request))
    if ReasoningCategory.FOLLOW_UP_RESEARCH_QUESTION in categories:
        statements.extend(_follow_up_questions(request))
    if request.literature_context is not None:
        statements.extend(_literature_statements(request))
    return sorted(statements, key=lambda item: item.statement_id)


def _empirical_interpretation(
    claim: ClaimCandidate, request: ReasoningRequest
) -> ReasoningStatement:
    relation = "is associated with"
    if claim.claim_type is ClaimType.CONDITIONAL_ASSOCIATION:
        relation = "is conditionally associated with"
    direction = _direction_text(claim.direction)
    controls = _controls_text(claim)
    text = (
        f"{claim.subject_variable or 'The modeled term'} {relation} "
        f"{claim.outcome_variable or 'the outcome'} in the {direction} direction "
        f"within the specified {claim.statistical_procedure.value} model{controls}. "
        "This is an empirical interpretation of a non-causal claim candidate."
    )
    return _statement(
        request,
        ReasoningCategory.EMPIRICAL_INTERPRETATION,
        text,
        claim_ids=(claim.claim_id,),
        evidence_ids=claim.supporting_evidence_ids,
        domains=_domains_for_claim(request, claim.claim_id),
        support_level=_support_level(request, (claim,)),
        epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
        limitations=tuple(code.value for code in claim.limitation_codes),
    )


def _cross_domain_statements(request: ReasoningRequest) -> tuple[ReasoningStatement, ...]:
    statements = []
    for record in request.coordinated_assessment.claim_domain_map:
        if record.cross_domain:
            statements.append(
                _statement(
                    request,
                    ReasoningCategory.CROSS_DOMAIN_SYNTHESIS,
                    (
                        f"Claim {record.claim_id} was selected by "
                        f"{_domain_list(record.selecting_domains)}, indicating shared "
                        "cross-domain relevance for the same structured non-causal evidence."
                    ),
                    claim_ids=(record.claim_id,),
                    domains=record.selecting_domains,
                    support_level=SupportLevel.MODERATE,
                    epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
                    limitations=tuple(code.value for code in record.shared_limitations),
                )
            )
    return tuple(statements)


def _mechanism_statements(request: ReasoningRequest) -> tuple[ReasoningStatement, ...]:
    statements = []
    for claim in _first_cross_domain_claims(request):
        statements.append(
            _statement(
                request,
                ReasoningCategory.PLAUSIBLE_MECHANISM,
                (
                    f"One plausible mechanism is that {claim.subject_variable or 'the exposure'} "
                    f"may plausibly contribute to conditions related to "
                    f"{claim.outcome_variable or 'the outcome'}, but the mechanism was not "
                    "directly tested and causality is not established."
                ),
                evidence_ids=claim.supporting_evidence_ids,
                claim_ids=(claim.claim_id,),
                domains=_domains_for_claim(request, claim.claim_id),
                support_level=SupportLevel.LIMITED,
                epistemic_status=EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN,
                causal_status=CausalStatus.NOT_ESTABLISHED,
                limitations=("mechanism not directly tested",),
            )
        )
    return tuple(statements)


def _alternative_explanations(request: ReasoningRequest) -> tuple[ReasoningStatement, ...]:
    claim = _primary_claim(request.evidence_artifact)
    if claim is None:
        return ()
    domains = _domains_for_claim(request, claim.claim_id)
    templates = (
        (
            "Reverse ordering or simultaneous relationships could account for the observed "
            f"association involving {claim.subject_variable or 'the exposure'} and "
            f"{claim.outcome_variable or 'the outcome'}."
        ),
        (
            "An omitted variable related to economic resources, institutional capacity, "
            "health-system capacity, education, demographic structure, or regional composition "
            "could partly account for the observed association."
        ),
    )
    return tuple(
        _statement(
            request,
            ReasoningCategory.ALTERNATIVE_EXPLANATION,
            text + " This is an alternative explanation, not an established finding.",
            evidence_ids=claim.supporting_evidence_ids,
            claim_ids=(claim.claim_id,),
            domains=domains,
            support_level=SupportLevel.LIMITED,
            epistemic_status=EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN,
            causal_status=CausalStatus.NOT_ESTABLISHED,
            limitations=("alternative explanation not directly tested",),
        )
        for text in templates
    )


def _confounder_statements(request: ReasoningRequest) -> tuple[ReasoningStatement, ...]:
    evidence_ids = {record.evidence_id for record in request.evidence_artifact.evidence_records}
    claim_ids = {claim.claim_id for claim in request.evidence_artifact.claim_candidates}
    return tuple(
        _statement(
            request,
            ReasoningCategory.POTENTIAL_CONFOUNDER,
            (
                f"{item.variable_or_concept} is a potential confounder or candidate control: "
                f"{item.reason_it_may_matter}"
            ),
            evidence_ids=tuple(
                source for source in item.supporting_source_ids if source in evidence_ids
            ),
            claim_ids=tuple(source for source in item.supporting_source_ids if source in claim_ids),
            domains=item.related_domains,
            support_level=SupportLevel.LIMITED,
            epistemic_status=EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN,
            causal_status=CausalStatus.NOT_ESTABLISHED,
            limitations=("candidate confounder status not established",),
        )
        for item in _candidate_confounders(request)
    )


def _limitation_statements(request: ReasoningRequest) -> tuple[ReasoningStatement, ...]:
    limitations = sorted(
        {
            *(
                code
                for record in request.evidence_artifact.evidence_records
                for code in record.limitation_codes
            ),
            *(
                code
                for claim in request.evidence_artifact.claim_candidates
                for code in claim.limitation_codes
            ),
            *(
                record.limitation_code
                for record in request.coordinated_assessment.shared_limitations
            ),
        },
        key=lambda item: item.value,
    )
    if not limitations:
        limitations = [LimitationCode.OBSERVATIONAL_ASSOCIATION]
    primary = _primary_claim(request.evidence_artifact)
    claim_ids = (primary.claim_id,) if primary is not None else ()
    evidence_ids = (
        primary.supporting_evidence_ids if primary is not None else _first_evidence_ids(request)
    )
    return tuple(
        _statement(
            request,
            ReasoningCategory.LIMITATION,
            (
                f"Limitation {code.value} constrains interpretation; the current evidence "
                "supports descriptive or associational conclusions only."
            ),
            evidence_ids=evidence_ids,
            claim_ids=claim_ids,
            domains=request.coordinated_assessment.participating_domains,
            support_level=SupportLevel.STRONG,
            epistemic_status=EpistemicStatus.DIRECTLY_SUPPORTED,
            limitations=(code.value,),
        )
        for code in limitations
    )


def _follow_up_hypotheses(request: ReasoningRequest) -> tuple[ReasoningStatement, ...]:
    claim = _primary_claim(request.evidence_artifact)
    if claim is None:
        return ()
    text = (
        f"The association between {claim.subject_variable or 'the exposure'} and "
        f"{claim.outcome_variable or 'the outcome'} may differ across countries with different "
        "levels of candidate controls represented in the project."
    )
    return (
        _statement(
            request,
            ReasoningCategory.FOLLOW_UP_HYPOTHESIS,
            text,
            evidence_ids=claim.supporting_evidence_ids,
            claim_ids=(claim.claim_id,),
            domains=_domains_for_claim(request, claim.claim_id),
            support_level=SupportLevel.LIMITED,
            epistemic_status=EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN,
            causal_status=CausalStatus.NOT_ESTABLISHED,
            limitations=("exploratory follow-up hypothesis",),
        ),
    )


def _follow_up_questions(request: ReasoningRequest) -> tuple[ReasoningStatement, ...]:
    claim = _primary_claim(request.evidence_artifact)
    if claim is None:
        return ()
    variables = sorted(
        {
            variable
            for evidence in request.evidence_artifact.evidence_records
            for variable in _evidence_variables(evidence)
        }
    )
    exposure = claim.subject_variable or (variables[0] if variables else "the exposure")
    outcome = claim.outcome_variable or "the outcome"
    question_one = (
        f"Is the association between {exposure} and {outcome} stable across alternative "
        "model specifications using currently available Polaris variables?"
    )
    question_two = (
        f"Do candidate controls such as {', '.join(variables[:3]) or 'available covariates'} "
        f"attenuate the association between {exposure} and {outcome}?"
    )
    return tuple(
        _statement(
            request,
            ReasoningCategory.FOLLOW_UP_RESEARCH_QUESTION,
            text,
            evidence_ids=claim.supporting_evidence_ids,
            claim_ids=(claim.claim_id,),
            domains=_domains_for_claim(request, claim.claim_id),
            support_level=SupportLevel.LIMITED,
            epistemic_status=EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN,
            causal_status=CausalStatus.NOT_ESTABLISHED,
            limitations=("follow-up question, not an established conclusion",),
        )
        for text in (question_one, question_two)
    )


def _literature_statements(request: ReasoningRequest) -> tuple[ReasoningStatement, ...]:
    literature = request.literature_context
    if literature is None:
        return ()
    statements = []
    by_claim = {claim.claim_id: claim for claim in request.evidence_artifact.claim_candidates}
    for record in literature.literature_evidence:
        claim = by_claim.get(record.empirical_claim_id)
        if claim is None:
            continue
        if record.support_classification is LiteratureSupportClassification.SUPPORTING:
            category = ReasoningCategory.LITERATURE_ALIGNMENT
            text = (
                f"Literature evidence {record.literature_evidence_id} is classified as "
                f"supporting context for empirical claim {claim.claim_id}; it remains "
                "contextual and does not validate the Polaris statistical finding."
            )
        elif record.support_classification is LiteratureSupportClassification.CONTRASTING:
            category = ReasoningCategory.LITERATURE_CONTRAST
            text = (
                f"Literature evidence {record.literature_evidence_id} contrasts with "
                f"empirical claim {claim.claim_id}; the contrast should remain unresolved "
                "unless follow-up analysis addresses it."
            )
        else:
            continue
        statements.append(
            _statement(
                request,
                category,
                text,
                claim_ids=(claim.claim_id,),
                literature_ids=(record.literature_evidence_id,),
                domains=_domains_for_claim(request, claim.claim_id),
                support_level=SupportLevel.MODERATE,
                epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
                limitations=("literature is contextual rather than empirical validation",),
            )
        )
    return tuple(statements)


def _contradictions(request: ReasoningRequest) -> tuple[ContradictionRecord, ...]:
    records: list[ContradictionRecord] = []
    by_pair: dict[tuple[str | None, str | None], list[ClaimCandidate]] = defaultdict(list)
    for claim in request.evidence_artifact.claim_candidates:
        by_pair[(claim.subject_variable, claim.outcome_variable)].append(claim)
    for claims in by_pair.values():
        directions = {claim.direction for claim in claims}
        if Direction.POSITIVE in directions and Direction.NEGATIVE in directions:
            left = next(claim for claim in claims if claim.direction is Direction.POSITIVE)
            right = next(claim for claim in claims if claim.direction is Direction.NEGATIVE)
            records.append(
                ContradictionRecord(
                    contradiction_id=deterministic_id(
                        "contradiction_",
                        {
                            "left": left.claim_id,
                            "right": right.claim_id,
                            "schema_version": REASONING_SCHEMA_VERSION,
                        },
                    ),
                    claim_id_a=left.claim_id,
                    claim_id_b=right.claim_id,
                    nature_of_conflict="claim candidates have opposing effect directions",
                    possible_explanation=(
                        "Different specifications, samples, or variable definitions may explain "
                        "the inconsistent pattern."
                    ),
                )
            )
    if request.literature_context is not None:
        for item in request.literature_context.literature_evidence:
            if item.support_classification is LiteratureSupportClassification.CONTRASTING:
                records.append(
                    ContradictionRecord(
                        contradiction_id=deterministic_id(
                            "contradiction_",
                            {
                                "claim": item.empirical_claim_id,
                                "literature": item.literature_evidence_id,
                                "schema_version": REASONING_SCHEMA_VERSION,
                            },
                        ),
                        claim_id_a=item.empirical_claim_id,
                        literature_evidence_id=item.literature_evidence_id,
                        nature_of_conflict="literature context contrasts with empirical claim",
                        possible_explanation=(
                            "Corpus scope, methods, populations, or measurement differences may "
                            "account for the contrast."
                        ),
                    )
                )
    return tuple(sorted(records, key=lambda item: item.contradiction_id))


def _candidate_confounders(request: ReasoningRequest) -> tuple[CandidateConfounder, ...]:
    primary = _primary_claim(request.evidence_artifact)
    if primary is None:
        return ()
    measured = {
        variable
        for record in request.evidence_artifact.evidence_records
        for variable in _evidence_variables(record)
    }
    controlled = set(primary.related_variables)
    candidates = [
        ("GDP per capita", AgentDomain.ECONOMICS),
        ("healthcare access", AgentDomain.PUBLIC_HEALTH),
        ("education", AgentDomain.EDUCATION),
        ("institutional capacity", AgentDomain.GOVERNANCE),
    ]
    records = []
    for concept, domain in candidates:
        currently_measured = any(_matches_concept(variable, concept) for variable in measured)
        currently_controlled = any(_matches_concept(variable, concept) for variable in controlled)
        records.append(
            CandidateConfounder(
                confounder_id=deterministic_id(
                    "confounder_",
                    {
                        "concept": concept,
                        "claim_id": primary.claim_id,
                        "schema_version": REASONING_SCHEMA_VERSION,
                    },
                ),
                variable_or_concept=concept,
                reason_it_may_matter=(
                    "It could be related to both the exposure and outcome in an observational "
                    "cross-country association."
                ),
                currently_measured=currently_measured,
                currently_controlled=currently_controlled,
                related_domains=(domain,),
                supporting_source_ids=(primary.claim_id,),
            )
        )
    return tuple(sorted(records, key=lambda item: item.confounder_id))


def _support_level(request: ReasoningRequest, claims: tuple[ClaimCandidate, ...]) -> SupportLevel:
    if not claims:
        return SupportLevel.NONE
    directions = {claim.direction for claim in claims}
    if Direction.POSITIVE in directions and Direction.NEGATIVE in directions:
        return SupportLevel.MIXED
    if any(claim.confidence_interval_crosses_zero for claim in claims):
        return SupportLevel.LIMITED
    domain_counts = [
        record.selection_count
        for record in request.coordinated_assessment.claim_domain_map
        if record.claim_id in {claim.claim_id for claim in claims}
    ]
    if len(claims) >= 2 and max(domain_counts or [0]) >= 2:
        return SupportLevel.STRONG
    if max(domain_counts or [0]) >= 2:
        return SupportLevel.MODERATE
    return SupportLevel.LIMITED


def _statement(
    request: ReasoningRequest,
    category: ReasoningCategory,
    text: str,
    *,
    evidence_ids: tuple[str, ...] = (),
    claim_ids: tuple[str, ...] = (),
    agent_ids: tuple[str, ...] = (),
    literature_ids: tuple[str, ...] = (),
    domains: tuple[AgentDomain, ...] = (),
    support_level: SupportLevel,
    epistemic_status: EpistemicStatus,
    causal_status: CausalStatus = CausalStatus.NON_CAUSAL,
    limitations: tuple[str, ...] = (),
) -> ReasoningStatement:
    return ReasoningStatement(
        statement_id=deterministic_id(
            "reasoning_statement_",
            {
                "category": category.value,
                "text": text,
                "evidence_ids": evidence_ids,
                "claim_ids": claim_ids,
                "agent_ids": agent_ids,
                "literature_ids": literature_ids,
                "schema_version": REASONING_SCHEMA_VERSION,
            },
        ),
        category=category,
        text=text,
        evidence_ids=evidence_ids,
        claim_ids=claim_ids,
        agent_assessment_ids=agent_ids or request.coordinated_assessment.source_assessment_ids,
        literature_evidence_ids=literature_ids,
        domains=domains or request.coordinated_assessment.participating_domains,
        support_level=support_level,
        epistemic_status=epistemic_status,
        causal_status=causal_status,
        limitations=limitations,
        provenance={"ruleset_version": REASONING_RULESET_VERSION},
    )


def _grounding_summary(
    *,
    statements: tuple[ReasoningStatement, ...],
    contradictions: tuple[ContradictionRecord, ...],
    confounders: tuple[CandidateConfounder, ...],
    rejected_provider_statements: int,
    unsupported_grounding_attempts: int,
    causal_guard_violations: int,
) -> GroundingSummary:
    return GroundingSummary(
        total_statements=len(statements),
        fully_grounded_statements=len(statements),
        statements_with_literature_support=sum(
            1 for item in statements if item.literature_evidence_ids
        ),
        statements_based_only_on_empirical_evidence=sum(
            1
            for item in statements
            if (item.evidence_ids or item.claim_ids) and not item.literature_evidence_ids
        ),
        plausible_or_unproven_statements=sum(
            1
            for item in statements
            if item.epistemic_status is EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN
        ),
        contradiction_count=len(contradictions),
        potential_confounder_count=len(confounders),
        follow_up_hypothesis_count=sum(
            1 for item in statements if item.category is ReasoningCategory.FOLLOW_UP_HYPOTHESIS
        ),
        follow_up_research_question_count=sum(
            1
            for item in statements
            if item.category is ReasoningCategory.FOLLOW_UP_RESEARCH_QUESTION
        ),
        rejected_provider_statements=rejected_provider_statements,
        unsupported_grounding_attempts=unsupported_grounding_attempts,
        causal_guard_violations=causal_guard_violations,
    )


def _primary_claim(evidence: EvidenceArtifact) -> ClaimCandidate | None:
    claims = [
        claim
        for claim in evidence.claim_candidates
        if claim.claim_type in {ClaimType.ASSOCIATION, ClaimType.CONDITIONAL_ASSOCIATION}
    ]
    return sorted(claims, key=lambda item: item.claim_id)[0] if claims else None


def _first_cross_domain_claims(request: ReasoningRequest) -> tuple[ClaimCandidate, ...]:
    cross_claim_ids = {
        record.claim_id
        for record in request.coordinated_assessment.claim_domain_map
        if record.cross_domain
    }
    claims = [
        claim
        for claim in request.evidence_artifact.claim_candidates
        if claim.claim_id in cross_claim_ids
    ]
    if not claims:
        primary = _primary_claim(request.evidence_artifact)
        return (primary,) if primary is not None else ()
    return tuple(sorted(claims, key=lambda item: item.claim_id)[:2])


def _domains_for_claim(request: ReasoningRequest, claim_id: str) -> tuple[AgentDomain, ...]:
    for record in request.coordinated_assessment.claim_domain_map:
        if record.claim_id == claim_id:
            return record.selecting_domains
    return request.coordinated_assessment.participating_domains


def _first_evidence_ids(request: ReasoningRequest) -> tuple[str, ...]:
    return tuple(record.evidence_id for record in request.evidence_artifact.evidence_records[:1])


def _direction_text(direction: Direction) -> str:
    if direction is Direction.POSITIVE:
        return "positive"
    if direction is Direction.NEGATIVE:
        return "negative"
    if direction is Direction.ZERO:
        return "near-zero"
    return "undefined"


def _controls_text(claim: ClaimCandidate) -> str:
    if claim.related_variables:
        return f", accounting for {', '.join(claim.related_variables)}"
    return ""


def _domain_list(domains: tuple[AgentDomain, ...]) -> str:
    return ", ".join(domain.value for domain in domains) or "no domains"


def _evidence_variables(record) -> tuple[str, ...]:
    variables: list[str] = []
    for name in (
        "variable_id",
        "variable_id_1",
        "variable_id_2",
        "dependent_variable_id",
        "predictor_variable_ids",
        "required_variable_ids",
        "variable_ids",
    ):
        value = getattr(record, name, None)
        if value is None:
            continue
        if isinstance(value, tuple):
            variables.extend(value)
        else:
            variables.append(value)
    if (
        getattr(record, "evidence_type", None) is EvidenceType.REGRESSION_COEFFICIENT
        and isinstance(record, RegressionCoefficientEvidenceRecord)
        and record.variable_id is not None
    ):
        variables.append(record.variable_id)
    return tuple(sorted(set(variables)))


def _matches_concept(variable: str, concept: str) -> bool:
    words = {word for word in concept.lower().replace("_", " ").split() if len(word) > 2}
    lowered = variable.lower().replace("_", " ")
    return any(word in lowered for word in words)
