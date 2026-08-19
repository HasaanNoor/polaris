"""Evidence-fidelity evaluation."""

from polaris.evaluation.models import (
    BenchmarkCase,
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
)
from polaris.evidence.models import ClaimType, Direction
from polaris.reasoning.models import ReasoningArtifact
from polaris.reasoning.taxonomy import ReasoningCategory, SupportLevel


def evaluate_evidence_fidelity(
    *,
    case: BenchmarkCase,
    reasoning: ReasoningArtifact,
) -> DimensionEvaluationResult:
    findings: list[EvaluationFinding] = []
    checks = 0
    passes = 0
    association_claims = [
        claim
        for claim in case.evidence_artifact.claim_candidates
        if claim.claim_type
        in {
            ClaimType.ASSOCIATION,
            ClaimType.CONDITIONAL_ASSOCIATION,
            ClaimType.CAUSAL_DESIGN_ESTIMATE,
        }
    ]
    empirical_statements = [
        item
        for item in reasoning.reasoning_statements
        if item.category is ReasoningCategory.EMPIRICAL_INTERPRETATION
    ]
    for claim in association_claims:
        related = [
            item
            for item in empirical_statements
            if claim.claim_id in item.claim_ids
            or set(claim.supporting_evidence_ids) & set(item.evidence_ids)
        ]
        if not related:
            continue
        checks += 1
        if all(_statement_preserves_direction(item.text, claim.direction) for item in related):
            passes += 1
        else:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.EVIDENCE_DIRECTION_MISMATCH,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.EVIDENCE_FIDELITY,
                    message="Reasoning direction conflicts with structured evidence direction.",
                    source_ids=(claim.claim_id, *claim.supporting_evidence_ids),
                    statement_ids=tuple(item.statement_id for item in related),
                )
            )
        if claim.claim_type is ClaimType.CONDITIONAL_ASSOCIATION:
            checks += 1
            if any(
                "conditional" in item.text.lower() or "account" in item.text.lower()
                for item in related
            ):
                passes += 1
            else:
                findings.append(
                    EvaluationFinding(
                        code=EvaluationFindingCode.CONDITIONALITY_LOST,
                        severity=EvaluationSeverity.ERROR,
                        dimension=EvaluationDimension.EVIDENCE_FIDELITY,
                        message="Reasoning did not preserve conditional model framing.",
                        source_ids=(claim.claim_id,),
                        statement_ids=tuple(item.statement_id for item in related),
                    )
                )
        if claim.p_value_below_threshold is False or claim.confidence_interval_crosses_zero is True:
            checks += 1
            overstated = [
                item
                for item in related
                if item.support_level is SupportLevel.STRONG
                or "strong" in item.text.lower()
                or "clear" in item.text.lower()
            ]
            if not overstated:
                passes += 1
            else:
                findings.append(
                    EvaluationFinding(
                        code=EvaluationFindingCode.OVERSTATED_SIGNIFICANCE,
                        severity=EvaluationSeverity.ERROR,
                        dimension=EvaluationDimension.EVIDENCE_FIDELITY,
                        message="Reasoning overstated weak or non-significant evidence.",
                        source_ids=(claim.claim_id,),
                        statement_ids=tuple(item.statement_id for item in overstated),
                    )
                )
    if case.expected_behavior.expected_direction is not None:
        checks += 1
        if any(
            _statement_preserves_direction(item.text, case.expected_behavior.expected_direction)
            for item in empirical_statements
        ):
            passes += 1
        else:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.EVIDENCE_DIRECTION_MISMATCH,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.EVIDENCE_FIDELITY,
                    message=(
                        "Expected evidence direction was not represented in empirical reasoning."
                    ),
                )
            )
    pass_rate = passes / checks if checks else 1.0
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.EVIDENCE_FIDELITY,
        passed=not findings,
        findings=tuple(findings),
        metrics={"fidelity_checks": checks, "fidelity_passes": passes, "pass_rate": pass_rate},
    )


def _statement_preserves_direction(text: str, direction: Direction) -> bool:
    lowered = text.lower()
    if direction is Direction.POSITIVE:
        return "positive" in lowered and "negative" not in lowered
    if direction is Direction.NEGATIVE:
        return "negative" in lowered and "positive" not in lowered
    if direction is Direction.ZERO:
        return "zero" in lowered or "non-significant" in lowered or "weak" in lowered
    return True
