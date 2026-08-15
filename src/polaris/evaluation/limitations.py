"""Material limitation propagation evaluation."""

from polaris.evaluation.models import (
    BenchmarkCase,
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
)
from polaris.reasoning.models import ReasoningArtifact


def evaluate_limitation_propagation(
    *,
    case: BenchmarkCase,
    reasoning: ReasoningArtifact,
) -> DimensionEvaluationResult:
    expected = tuple(item.lower() for item in case.expected_behavior.expected_limitations)
    represented_text = " ".join(
        statement.text.lower() for statement in reasoning.reasoning_statements
    )
    represented_limitations = {
        limitation.lower()
        for statement in reasoning.reasoning_statements
        for limitation in statement.limitations
    }
    findings: list[EvaluationFinding] = []
    covered = 0
    for limitation in expected:
        if (
            limitation in represented_limitations
            or limitation.replace("_", " ") in represented_text
        ):
            covered += 1
        else:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.MATERIAL_LIMITATION_DROPPED,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.LIMITATION_PROPAGATION,
                    message=f"Material limitation was not propagated: {limitation}",
                )
            )
    coverage = covered / len(expected) if expected else 1.0
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.LIMITATION_PROPAGATION,
        passed=not findings,
        findings=tuple(findings),
        metrics={
            "expected_material_limitation_count": len(expected),
            "covered_material_limitation_count": covered,
            "material_limitation_coverage": coverage,
        },
    )
