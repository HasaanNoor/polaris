"""Internal analytical reference index for Phase 9 reports."""

from polaris.coordination.models import CoordinatedAssessment
from polaris.evidence.models import EvidenceArtifact
from polaris.reporting.models import ReferenceIndexEntry, ReferenceKind


def build_reference_index(
    *,
    evidence_artifact: EvidenceArtifact,
    coordinated_assessment: CoordinatedAssessment,
    source_artifact_ids: tuple[str, ...],
) -> tuple[ReferenceIndexEntry, ...]:
    entries: list[ReferenceIndexEntry] = []
    for record in evidence_artifact.evidence_records:
        entries.append(
            ReferenceIndexEntry(
                reference_id=record.evidence_id,
                reference_kind=ReferenceKind.EVIDENCE,
                label=f"Evidence record: {record.evidence_type.value}",
                metadata={
                    "evidence_type": record.evidence_type.value,
                    "statistical_procedure": record.statistical_procedure.value,
                    "source_analysis_result_id": record.source_analysis_result_id,
                },
            )
        )
    for claim in evidence_artifact.claim_candidates:
        entries.append(
            ReferenceIndexEntry(
                reference_id=claim.claim_id,
                reference_kind=ReferenceKind.CLAIM,
                label=f"Claim candidate: {claim.claim_type.value}",
                metadata={
                    "claim_type": claim.claim_type.value,
                    "supporting_evidence_ids": list(claim.supporting_evidence_ids),
                    "causal": claim.causal,
                },
            )
        )
    for assessment_id in coordinated_assessment.source_assessment_ids:
        domain = next(
            (
                record.domain.value
                for record in coordinated_assessment.domain_coverage
                if record.assessment_id == assessment_id
            ),
            "unknown",
        )
        entries.append(
            ReferenceIndexEntry(
                reference_id=assessment_id,
                reference_kind=ReferenceKind.ASSESSMENT,
                label=f"Domain assessment: {domain}",
                metadata={"domain": domain},
            )
        )
    for agreement in coordinated_assessment.agreements:
        entries.append(
            ReferenceIndexEntry(
                reference_id=agreement.agreement_id,
                reference_kind=ReferenceKind.AGREEMENT,
                label=f"Coordination agreement: {agreement.agreement_type.value}",
                metadata={
                    "agreement_type": agreement.agreement_type.value,
                    "source_ids": list(agreement.source_ids),
                    "domains": [domain.value for domain in agreement.participating_domains],
                },
            )
        )
    for divergence in coordinated_assessment.divergences:
        entries.append(
            ReferenceIndexEntry(
                reference_id=divergence.divergence_id,
                reference_kind=ReferenceKind.DIVERGENCE,
                label=f"Coordination divergence: {divergence.divergence_type.value}",
                metadata={
                    "divergence_type": divergence.divergence_type.value,
                    "source_ids": list(divergence.source_ids),
                    "domains": [domain.value for domain in divergence.domains_involved],
                },
            )
        )
    for gap in coordinated_assessment.evidence_gaps:
        entries.append(
            ReferenceIndexEntry(
                reference_id=gap.gap_id,
                reference_kind=ReferenceKind.GAP,
                label=f"Evidence gap: {gap.gap_type.value}",
                metadata={
                    "gap_type": gap.gap_type.value,
                    "source_ids": list(gap.source_ids),
                    "domains": [domain.value for domain in gap.domains],
                },
            )
        )
    for gap in coordinated_assessment.domain_gaps:
        entries.append(
            ReferenceIndexEntry(
                reference_id=gap.gap_id,
                reference_kind=ReferenceKind.GAP,
                label=f"Domain gap: {gap.domain.value}",
                metadata={
                    "gap_type": gap.gap_type.value,
                    "domain": gap.domain.value,
                    "assessment_supplied": gap.assessment_supplied,
                },
            )
        )
    for artifact_id in source_artifact_ids:
        entries.append(
            ReferenceIndexEntry(
                reference_id=artifact_id,
                reference_kind=ReferenceKind.SOURCE_ARTIFACT,
                label="Source Polaris artifact",
                metadata={},
            )
        )
    return tuple(sorted(entries, key=lambda item: (item.reference_kind.value, item.reference_id)))
