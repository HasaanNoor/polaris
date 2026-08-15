"""Structural-validity evaluation."""

from polaris.evaluation.models import (
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
)
from polaris.reasoning.models import ReasoningArtifact


def evaluate_structural_validity(reasoning: ReasoningArtifact) -> DimensionEvaluationResult:
    findings: list[EvaluationFinding] = []
    ids = [statement.statement_id for statement in reasoning.reasoning_statements]
    if len(ids) != len(set(ids)):
        findings.append(
            EvaluationFinding(
                code=EvaluationFindingCode.STRUCTURAL_INVALIDITY,
                severity=EvaluationSeverity.ERROR,
                dimension=EvaluationDimension.STRUCTURAL_VALIDITY,
                message="Reasoning statements must have unique IDs.",
            )
        )
    for statement in reasoning.reasoning_statements:
        if not statement.text.strip():
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.STRUCTURAL_INVALIDITY,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.STRUCTURAL_VALIDITY,
                    message="Reasoning statement has empty substantive text.",
                    statement_ids=(statement.statement_id,),
                )
            )
    ordered = ids == sorted(ids)
    if not ordered:
        findings.append(
            EvaluationFinding(
                code=EvaluationFindingCode.STRUCTURAL_INVALIDITY,
                severity=EvaluationSeverity.WARNING,
                dimension=EvaluationDimension.STRUCTURAL_VALIDITY,
                message="Reasoning statements are not in deterministic statement-ID order.",
            )
        )
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.STRUCTURAL_VALIDITY,
        passed=not any(item.severity is EvaluationSeverity.ERROR for item in findings),
        findings=tuple(findings),
        metrics={
            "statement_count": len(ids),
            "unique_statement_ids": len(ids) == len(set(ids)),
            "deterministic_ordering": ordered,
        },
    )
