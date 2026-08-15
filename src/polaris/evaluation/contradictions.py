"""Contradiction-handling evaluation."""

from polaris.evaluation.models import (
    BenchmarkCase,
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
)
from polaris.reasoning.models import ReasoningArtifact
from polaris.reasoning.taxonomy import ReasoningCategory


def evaluate_contradiction_handling(
    *,
    case: BenchmarkCase,
    reasoning: ReasoningArtifact,
) -> DimensionEvaluationResult:
    expected = case.expected_behavior.expected_contradictions
    represented = len(reasoning.contradictions)
    category_statements = [
        statement
        for statement in reasoning.reasoning_statements
        if statement.category is ReasoningCategory.CONTRADICTION
    ]
    findings: list[EvaluationFinding] = []
    if expected and not represented and not category_statements:
        findings.append(
            EvaluationFinding(
                code=EvaluationFindingCode.CONTRADICTION_IGNORED,
                severity=EvaluationSeverity.ERROR,
                dimension=EvaluationDimension.CONTRADICTION_HANDLING,
                message="Expected conflicting evidence was not represented as a contradiction.",
                source_ids=expected,
            )
        )
    for record in reasoning.contradictions:
        grounded_sides = tuple(
            source
            for source in (
                record.evidence_id_a,
                record.evidence_id_b,
                record.claim_id_a,
                record.claim_id_b,
                record.literature_evidence_id,
            )
            if source is not None
        )
        if len(grounded_sides) < 2:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.INVALID_GROUNDING,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.CONTRADICTION_HANDLING,
                    message="Contradiction did not preserve grounded conflicting sides.",
                    source_ids=grounded_sides,
                )
            )
    rate = 1.0 if not expected else float(bool(represented or category_statements))
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.CONTRADICTION_HANDLING,
        passed=not findings,
        findings=tuple(findings),
        metrics={
            "expected_contradiction_count": len(expected),
            "represented_contradiction_count": represented + len(category_statements),
            "contradiction_detection_rate": rate,
        },
    )
