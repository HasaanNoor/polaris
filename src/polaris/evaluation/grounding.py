"""Grounding evaluation for reasoning artifacts."""

from polaris.evaluation.models import (
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
)
from polaris.reasoning.grounding import ReasoningGroundingIndex
from polaris.reasoning.models import ReasoningArtifact, ReasoningRequest
from polaris.reasoning.taxonomy import ReasoningCategory


def evaluate_grounding(
    *,
    request: ReasoningRequest,
    reasoning: ReasoningArtifact,
) -> DimensionEvaluationResult:
    index = ReasoningGroundingIndex(
        evidence_artifact=request.evidence_artifact,
        coordinated_assessment=request.coordinated_assessment,
        literature_context=request.literature_context,
    )
    findings: list[EvaluationFinding] = []
    grounded_count = 0
    invalid_count = 0
    orphan_count = 0
    for statement in reasoning.reasoning_statements:
        source_ids = (
            statement.evidence_ids
            + statement.claim_ids
            + statement.agent_assessment_ids
            + statement.literature_evidence_ids
        )
        if not source_ids:
            orphan_count += 1
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.ORPHAN_STATEMENT,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.GROUNDING,
                    message="Reasoning statement has no grounding references.",
                    statement_ids=(statement.statement_id,),
                )
            )
            continue
        missing = index.unsupported_ids(statement)
        if missing:
            invalid_count += len(missing)
            code = EvaluationFindingCode.FABRICATED_CITATION
            if set(missing) - set(statement.literature_evidence_ids):
                code = EvaluationFindingCode.INVALID_GROUNDING
            findings.append(
                EvaluationFinding(
                    code=code,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.GROUNDING,
                    message="Reasoning statement referenced unsupported grounding IDs.",
                    source_ids=missing,
                    statement_ids=(statement.statement_id,),
                )
            )
        else:
            grounded_count += 1
        if statement.literature_evidence_ids and statement.category not in {
            ReasoningCategory.LITERATURE_ALIGNMENT,
            ReasoningCategory.LITERATURE_CONTRAST,
            ReasoningCategory.FOLLOW_UP_RESEARCH_QUESTION,
            ReasoningCategory.FOLLOW_UP_HYPOTHESIS,
        }:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.LITERATURE_AS_EMPIRICAL_EVIDENCE,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.GROUNDING,
                    message="Literature grounding was attached to a non-literature statement.",
                    source_ids=statement.literature_evidence_ids,
                    statement_ids=(statement.statement_id,),
                )
            )
    count = len(reasoning.reasoning_statements)
    coverage = grounded_count / count if count else 0.0
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.GROUNDING,
        passed=not findings,
        findings=tuple(findings),
        metrics={
            "statement_count": count,
            "grounded_statement_count": grounded_count,
            "invalid_grounding_count": invalid_count,
            "orphan_statement_count": orphan_count,
            "grounding_coverage_ratio": coverage,
        },
    )
