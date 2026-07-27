"""Agreement and divergence identification for Phase 7 coordination."""

from collections import defaultdict

from polaris.agents.models import (
    AgentAssessment,
    AgentDomain,
    DomainConcernCode,
    UnsupportedInferenceCode,
)
from polaris.coordination.models import (
    COORDINATION_RULESET_VERSION,
    COORDINATION_SCHEMA_VERSION,
    AgreementType,
    CoordinationAgreement,
    CoordinationDivergence,
    DivergenceType,
    EvidenceDomainMapRecord,
)
from polaris.evidence.models import LimitationCode
from polaris.evidence.provenance import deterministic_id


def identify_agreements(
    assessments: tuple[AgentAssessment, ...],
    *,
    evidence_map: tuple[EvidenceDomainMapRecord, ...],
    claim_map: tuple,
) -> tuple[CoordinationAgreement, ...]:
    agreements: list[CoordinationAgreement] = []
    agreements.extend(
        _agreement(
            AgreementType.SHARED_EVIDENCE,
            source_ids=(record.evidence_id,),
            domains=record.selecting_domains,
        )
        for record in evidence_map
        if record.cross_domain
    )
    agreements.extend(
        _agreement(
            AgreementType.SHARED_CLAIM,
            source_ids=(record.claim_id,),
            limitation_codes=record.shared_limitations,
            domains=record.selecting_domains,
        )
        for record in claim_map
        if record.cross_domain
    )
    agreements.extend(_shared_limitation_agreements(assessments))
    agreements.extend(_shared_unsupported_agreements(assessments))
    agreements.extend(_shared_concern_agreements(assessments))
    return tuple(
        sorted(agreements, key=lambda item: (item.agreement_type.value, item.agreement_id))
    )


def identify_divergences(
    assessments: tuple[AgentAssessment, ...],
    *,
    evidence_map: tuple[EvidenceDomainMapRecord, ...],
    claim_map: tuple,
) -> tuple[CoordinationDivergence, ...]:
    divergences: list[CoordinationDivergence] = []
    divergences.extend(_different_relevance_classification(assessments))
    divergences.extend(_domain_specific_concerns(assessments))
    divergences.extend(_domain_specific_unsupported(assessments))
    divergences.extend(_domain_specific_limitations(assessments))
    divergences.extend(
        _uneven_coverage(assessments, evidence_map=evidence_map, claim_map=claim_map)
    )
    return tuple(
        sorted(divergences, key=lambda item: (item.divergence_type.value, item.divergence_id))
    )


def _shared_limitation_agreements(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[CoordinationAgreement, ...]:
    by_code: dict[LimitationCode, set[AgentDomain]] = defaultdict(set)
    for assessment in assessments:
        for code in assessment.inherited_limitations:
            by_code[code].add(assessment.agent_domain)
    return tuple(
        _agreement(
            AgreementType.SHARED_LIMITATION,
            limitation_codes=(code,),
            domains=tuple(domains),
        )
        for code, domains in by_code.items()
        if len(domains) > 1
    )


def _shared_unsupported_agreements(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[CoordinationAgreement, ...]:
    by_code: dict[UnsupportedInferenceCode, set[AgentDomain]] = defaultdict(set)
    for assessment in assessments:
        for code in assessment.unsupported_inferences:
            by_code[code].add(assessment.agent_domain)
    return tuple(
        _agreement(
            AgreementType.SHARED_UNSUPPORTED_INFERENCE,
            unsupported_inference_codes=(code,),
            domains=tuple(domains),
        )
        for code, domains in by_code.items()
        if len(domains) > 1
    )


def _shared_concern_agreements(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[CoordinationAgreement, ...]:
    by_code: dict[DomainConcernCode, set[AgentDomain]] = defaultdict(set)
    source_ids: dict[DomainConcernCode, set[str]] = defaultdict(set)
    for assessment in assessments:
        for concern in assessment.domain_concerns:
            by_code[concern.concern_code].add(assessment.agent_domain)
            source_ids[concern.concern_code].update(concern.source_ids)
    return tuple(
        _agreement(
            AgreementType.SHARED_DOMAIN_CONCERN,
            source_ids=tuple(source_ids[code]),
            domain_concern_codes=(code,),
            domains=tuple(domains),
        )
        for code, domains in by_code.items()
        if len(domains) > 1
    )


def _different_relevance_classification(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[CoordinationDivergence, ...]:
    selected_by_source: dict[str, set[AgentDomain]] = defaultdict(set)
    record_domains_by_source: dict[str, set[AgentDomain]] = defaultdict(set)
    for assessment in assessments:
        selected = set(assessment.relevant_evidence_ids) | set(assessment.relevant_claim_ids)
        for record in assessment.domain_relevance_records:
            record_domains_by_source[record.source_id].add(assessment.agent_domain)
            if record.source_id in selected:
                selected_by_source[record.source_id].add(assessment.agent_domain)
    participating = {assessment.agent_domain for assessment in assessments}
    return tuple(
        _divergence(
            DivergenceType.DIFFERENT_RELEVANCE_CLASSIFICATION,
            domains=tuple(record_domains_by_source[source_id] | selected_domains),
            source_ids=(source_id,),
            factual_basis="source selected by some supplied domains and not selected by others",
        )
        for source_id, selected_domains in selected_by_source.items()
        if selected_domains and selected_domains != participating
    )


def _domain_specific_concerns(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[CoordinationDivergence, ...]:
    by_code: dict[DomainConcernCode, set[AgentDomain]] = defaultdict(set)
    source_ids: dict[DomainConcernCode, set[str]] = defaultdict(set)
    for assessment in assessments:
        for concern in assessment.domain_concerns:
            by_code[concern.concern_code].add(assessment.agent_domain)
            source_ids[concern.concern_code].update(concern.source_ids)
    participating = {assessment.agent_domain for assessment in assessments}
    return tuple(
        _divergence(
            DivergenceType.DOMAIN_SPECIFIC_CONCERN,
            domains=tuple(domains),
            source_ids=tuple(source_ids[code]),
            domain_concern_codes=(code,),
            factual_basis="concern code appears in some supplied domains only",
        )
        for code, domains in by_code.items()
        if domains != participating
    )


def _domain_specific_unsupported(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[CoordinationDivergence, ...]:
    by_code: dict[UnsupportedInferenceCode, set[AgentDomain]] = defaultdict(set)
    for assessment in assessments:
        for code in assessment.unsupported_inferences:
            by_code[code].add(assessment.agent_domain)
    participating = {assessment.agent_domain for assessment in assessments}
    return tuple(
        _divergence(
            DivergenceType.DOMAIN_SPECIFIC_UNSUPPORTED_INFERENCE,
            domains=tuple(domains),
            unsupported_inference_codes=(code,),
            factual_basis="unsupported-inference code appears in some supplied domains only",
        )
        for code, domains in by_code.items()
        if domains != participating
    )


def _domain_specific_limitations(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[CoordinationDivergence, ...]:
    by_code: dict[LimitationCode, set[AgentDomain]] = defaultdict(set)
    for assessment in assessments:
        for code in assessment.inherited_limitations:
            by_code[code].add(assessment.agent_domain)
    participating = {assessment.agent_domain for assessment in assessments}
    return tuple(
        _divergence(
            DivergenceType.DOMAIN_SPECIFIC_LIMITATION,
            domains=tuple(domains),
            limitation_codes=(code,),
            factual_basis="limitation appears in some supplied domains only",
        )
        for code, domains in by_code.items()
        if domains != participating
    )


def _uneven_coverage(
    assessments: tuple[AgentAssessment, ...],
    *,
    evidence_map: tuple[EvidenceDomainMapRecord, ...],
    claim_map: tuple,
) -> tuple[CoordinationDivergence, ...]:
    participating = {assessment.agent_domain for assessment in assessments}
    source_domains = {
        **{record.evidence_id: set(record.selecting_domains) for record in evidence_map},
        **{record.claim_id: set(record.selecting_domains) for record in claim_map},
    }
    return tuple(
        _divergence(
            DivergenceType.UNEVEN_EVIDENCE_COVERAGE,
            domains=tuple(domains),
            source_ids=(source_id,),
            factual_basis="structured source coverage is uneven across supplied domains",
        )
        for source_id, domains in source_domains.items()
        if domains and domains != participating
    )


def _agreement(
    agreement_type: AgreementType,
    *,
    domains: tuple[AgentDomain, ...],
    source_ids: tuple[str, ...] = (),
    limitation_codes: tuple[LimitationCode, ...] = (),
    unsupported_inference_codes: tuple[UnsupportedInferenceCode, ...] = (),
    domain_concern_codes: tuple[DomainConcernCode, ...] = (),
) -> CoordinationAgreement:
    payload = {
        "agreement_type": agreement_type,
        "source_ids": tuple(sorted(source_ids)),
        "limitation_codes": tuple(sorted(limitation_codes, key=lambda item: item.value)),
        "unsupported_inference_codes": tuple(
            sorted(unsupported_inference_codes, key=lambda item: item.value)
        ),
        "domain_concern_codes": tuple(sorted(domain_concern_codes, key=lambda item: item.value)),
        "participating_domains": tuple(
            sorted(domains, key=lambda domain: tuple(AgentDomain).index(domain))
        ),
        "ruleset_version": COORDINATION_RULESET_VERSION,
        "schema_version": COORDINATION_SCHEMA_VERSION,
    }
    return CoordinationAgreement(
        agreement_id=deterministic_id("coordination_agreement_", payload),
        agreement_type=agreement_type,
        source_ids=source_ids,
        limitation_codes=limitation_codes,
        unsupported_inference_codes=unsupported_inference_codes,
        domain_concern_codes=domain_concern_codes,
        participating_domains=domains,
    )


def _divergence(
    divergence_type: DivergenceType,
    *,
    domains: tuple[AgentDomain, ...],
    factual_basis: str,
    source_ids: tuple[str, ...] = (),
    limitation_codes: tuple[LimitationCode, ...] = (),
    unsupported_inference_codes: tuple[UnsupportedInferenceCode, ...] = (),
    domain_concern_codes: tuple[DomainConcernCode, ...] = (),
) -> CoordinationDivergence:
    payload = {
        "divergence_type": divergence_type,
        "source_ids": tuple(sorted(source_ids)),
        "limitation_codes": tuple(sorted(limitation_codes, key=lambda item: item.value)),
        "unsupported_inference_codes": tuple(
            sorted(unsupported_inference_codes, key=lambda item: item.value)
        ),
        "domain_concern_codes": tuple(sorted(domain_concern_codes, key=lambda item: item.value)),
        "domains": tuple(sorted(domains, key=lambda domain: tuple(AgentDomain).index(domain))),
        "factual_basis": factual_basis,
        "ruleset_version": COORDINATION_RULESET_VERSION,
        "schema_version": COORDINATION_SCHEMA_VERSION,
    }
    return CoordinationDivergence(
        divergence_id=deterministic_id("coordination_divergence_", payload),
        divergence_type=divergence_type,
        domains_involved=domains,
        source_ids=source_ids,
        limitation_codes=limitation_codes,
        unsupported_inference_codes=unsupported_inference_codes,
        domain_concern_codes=domain_concern_codes,
        factual_basis=factual_basis,
    )
