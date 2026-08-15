"""Literature-separation evaluation."""

from polaris.evaluation.models import (
    BenchmarkCase,
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
    ExpectedLiteratureBehavior,
)
from polaris.reasoning.models import ReasoningArtifact
from polaris.reasoning.taxonomy import ReasoningCategory


def evaluate_literature_separation(
    *,
    case: BenchmarkCase,
    reasoning: ReasoningArtifact,
) -> DimensionEvaluationResult:
    findings: list[EvaluationFinding] = []
    literature_ids = (
        {record.literature_evidence_id for record in case.literature_context.literature_evidence}
        if case.literature_context is not None
        else set()
    )
    literature_statements = [
        statement
        for statement in reasoning.reasoning_statements
        if statement.category
        in {ReasoningCategory.LITERATURE_ALIGNMENT, ReasoningCategory.LITERATURE_CONTRAST}
    ]
    for statement in reasoning.reasoning_statements:
        missing = tuple(sorted(set(statement.literature_evidence_ids) - literature_ids))
        if missing:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.FABRICATED_CITATION,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.LITERATURE_SEPARATION,
                    message="Reasoning referenced unknown literature evidence IDs.",
                    source_ids=missing,
                    statement_ids=(statement.statement_id,),
                )
            )
        if statement.literature_evidence_ids and statement.category not in {
            ReasoningCategory.LITERATURE_ALIGNMENT,
            ReasoningCategory.LITERATURE_CONTRAST,
            ReasoningCategory.FOLLOW_UP_HYPOTHESIS,
            ReasoningCategory.FOLLOW_UP_RESEARCH_QUESTION,
        }:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.LITERATURE_AS_EMPIRICAL_EVIDENCE,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.LITERATURE_SEPARATION,
                    message=(
                        "Literature was used as empirical evidence rather than separate context."
                    ),
                    source_ids=statement.literature_evidence_ids,
                    statement_ids=(statement.statement_id,),
                )
            )
    behavior = case.expected_behavior.expected_literature_behavior
    if behavior is ExpectedLiteratureBehavior.ALIGNMENT and not any(
        item.category is ReasoningCategory.LITERATURE_ALIGNMENT for item in literature_statements
    ):
        findings.append(_missing_literature_behavior("Expected literature alignment was absent."))
    if behavior is ExpectedLiteratureBehavior.CONTRAST and not any(
        item.category is ReasoningCategory.LITERATURE_CONTRAST for item in literature_statements
    ):
        findings.append(_missing_literature_behavior("Expected literature contrast was absent."))
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.LITERATURE_SEPARATION,
        passed=not findings,
        findings=tuple(findings),
        metrics={
            "literature_evidence_count": len(literature_ids),
            "literature_statement_count": len(literature_statements),
            "fabricated_citation_count": sum(
                1 for item in findings if item.code is EvaluationFindingCode.FABRICATED_CITATION
            ),
        },
    )


def _missing_literature_behavior(message: str) -> EvaluationFinding:
    return EvaluationFinding(
        code=EvaluationFindingCode.EXPECTED_CATEGORY_MISSING,
        severity=EvaluationSeverity.ERROR,
        dimension=EvaluationDimension.LITERATURE_SEPARATION,
        message=message,
    )
