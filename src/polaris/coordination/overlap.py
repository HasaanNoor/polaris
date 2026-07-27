"""Cross-domain evidence, claim, limitation, and unsupported-inference mapping."""

from collections import defaultdict

from polaris.agents.models import (
    AgentAssessment,
    AgentDomain,
    DomainRelevanceRecord,
    RelevanceSourceType,
)
from polaris.coordination.models import (
    ClaimDomainMapRecord,
    DomainRelevanceReference,
    EvidenceDomainMapRecord,
    SharedLimitationRecord,
    UnsupportedInferenceAggregation,
)
from polaris.evidence.models import LimitationCode


def evidence_domain_map(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[EvidenceDomainMapRecord, ...]:
    return tuple(
        EvidenceDomainMapRecord(
            evidence_id=source_id,
            selecting_domains=domains,
            relevance_by_domain=_relevance_refs(records),
            selection_count=len(domains),
            cross_domain=len(domains) > 1,
        )
        for source_id, domains, records in _selected_source_groups(
            assessments, source_type=RelevanceSourceType.EVIDENCE_RECORD
        )
    )


def claim_domain_map(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[ClaimDomainMapRecord, ...]:
    return tuple(
        ClaimDomainMapRecord(
            claim_id=source_id,
            selecting_domains=domains,
            relevance_by_domain=_relevance_refs(records),
            shared_limitations=_shared_limitations_for_domains(assessments, domains),
            selection_count=len(domains),
            cross_domain=len(domains) > 1,
        )
        for source_id, domains, records in _selected_source_groups(
            assessments, source_type=RelevanceSourceType.CLAIM_CANDIDATE
        )
    )


def shared_limitations(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[SharedLimitationRecord, ...]:
    by_limitation: dict[LimitationCode, set[AgentDomain]] = defaultdict(set)
    source_ids: dict[LimitationCode, set[str]] = defaultdict(set)
    for assessment in assessments:
        selected_sources = set(assessment.relevant_evidence_ids) | set(
            assessment.relevant_claim_ids
        )
        for limitation in assessment.inherited_limitations:
            by_limitation[limitation].add(assessment.agent_domain)
        for concern in assessment.domain_concerns:
            for limitation in concern.limitation_codes:
                by_limitation[limitation].add(assessment.agent_domain)
                source_ids[limitation].update(concern.source_ids or selected_sources)
        for limitation in assessment.inherited_limitations:
            source_ids[limitation].update(selected_sources)
    participating = {assessment.agent_domain for assessment in assessments}
    return tuple(
        SharedLimitationRecord(
            limitation_code=limitation,
            domains=tuple(domains),
            associated_source_ids=tuple(source_ids[limitation]),
            global_limitation=domains == participating,
        )
        for limitation, domains in sorted(by_limitation.items(), key=lambda item: item[0].value)
    )


def unsupported_inference_aggregation(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[UnsupportedInferenceAggregation, ...]:
    by_code = defaultdict(set)
    claims_by_code = defaultdict(set)
    for assessment in assessments:
        for code in assessment.unsupported_inferences:
            by_code[code].add(assessment.agent_domain)
            claims_by_code[code].update(assessment.relevant_claim_ids)
    participating = {assessment.agent_domain for assessment in assessments}
    return tuple(
        UnsupportedInferenceAggregation(
            inference_code=code,
            domains=tuple(domains),
            all_participating_agents=domains == participating,
            relevant_claim_ids=tuple(claims_by_code[code]),
        )
        for code, domains in sorted(by_code.items(), key=lambda item: item[0].value)
    )


def _selected_source_groups(
    assessments: tuple[AgentAssessment, ...],
    *,
    source_type: RelevanceSourceType,
) -> tuple[tuple[str, tuple[AgentDomain, ...], tuple[DomainRelevanceRecord, ...]], ...]:
    selected: dict[str, set[AgentDomain]] = defaultdict(set)
    records_by_id: dict[str, list[DomainRelevanceRecord]] = defaultdict(list)
    for assessment in assessments:
        selected_ids = (
            set(assessment.relevant_evidence_ids)
            if source_type is RelevanceSourceType.EVIDENCE_RECORD
            else set(assessment.relevant_claim_ids)
        )
        for record in assessment.domain_relevance_records:
            if record.source_type is source_type and record.source_id in selected_ids:
                selected[record.source_id].add(assessment.agent_domain)
                records_by_id[record.source_id].append(record)
    groups = []
    for source_id in sorted(selected):
        domains = tuple(
            sorted(selected[source_id], key=lambda domain: tuple(AgentDomain).index(domain))
        )
        records = tuple(
            sorted(
                records_by_id[source_id],
                key=lambda record: tuple(AgentDomain).index(record.agent_domain),
            )
        )
        groups.append((source_id, domains, records))
    return tuple(groups)


def _relevance_refs(
    records: tuple[DomainRelevanceRecord, ...],
) -> tuple[DomainRelevanceReference, ...]:
    return tuple(
        DomainRelevanceReference(
            domain=record.agent_domain,
            relevance_status=record.relevance_status,
            relevance_reason_codes=record.relevance_reason_codes,
            matched_variable_ids=record.matched_variable_ids,
            matched_concept_categories=tuple(
                concept.value for concept in record.matched_concept_categories
            ),
        )
        for record in records
    )


def _shared_limitations_for_domains(
    assessments: tuple[AgentAssessment, ...],
    domains: tuple[AgentDomain, ...],
) -> tuple[LimitationCode, ...]:
    selected = [assessment for assessment in assessments if assessment.agent_domain in domains]
    if not selected:
        return ()
    common = set(selected[0].inherited_limitations)
    for assessment in selected[1:]:
        common &= set(assessment.inherited_limitations)
    return tuple(sorted(common, key=lambda item: item.value))
