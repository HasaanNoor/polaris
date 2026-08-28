"""Public service API for Phase 24 causal robustness analysis."""

from polaris.analysis.causal.models import CausalAnalysisResult
from polaris.analysis.robustness.models import (
    RealStudyReadinessBlock,
    RobustnessAnalysisResult,
    RobustnessSpecification,
)
from polaris.analysis.robustness.runner import run_robustness_analysis
from polaris.causal_studies.models import ReadinessStatus, ReviewStatus
from polaris.causal_studies.readiness import assess_design_readiness
from polaris.causal_studies.registry import CausalStudyRegistry, load_causal_study_registry
from polaris.ingestion.models import DatasetIngestionResult
from polaris.registry import DatasetRegistry


def analyze_robustness(
    *,
    ingestion_result: DatasetIngestionResult,
    baseline_result: CausalAnalysisResult,
    specification: RobustnessSpecification,
    significance_threshold: float | None = None,
) -> RobustnessAnalysisResult:
    """Run explicit robustness checks for a completed causal analysis."""

    return run_robustness_analysis(
        ingestion_result=ingestion_result,
        baseline_result=baseline_result,
        specification=specification,
        significance_threshold=significance_threshold,
    )


def assess_real_study_execution_readiness(
    *,
    registry: CausalStudyRegistry | None = None,
    dataset_registry: DatasetRegistry | None = None,
    ingestion_results: tuple[DatasetIngestionResult, ...] = (),
) -> tuple[RealStudyReadinessBlock, ...]:
    """Report why currently registered studies are or are not executable."""

    active = registry or load_causal_study_registry()
    blocks = []
    for study in active.list_studies():
        assessment = assess_design_readiness(
            study,
            registry=dataset_registry,
            ingestion_results=ingestion_results,
        )
        reasons = tuple(item.message for item in assessment.blocking_findings)
        if (
            study.review_status is not ReviewStatus.DESIGN_READY
            and assessment.readiness_status is not ReadinessStatus.READY
        ):
            reasons = (
                *reasons,
                "study is not reviewed as DESIGN_READY in the Phase 23 registry",
            )
        blocks.append(
            RealStudyReadinessBlock(
                study_id=study.study_id,
                readiness_status=assessment.readiness_status.value,
                review_status=study.review_status.value,
                blocking_reasons=tuple(sorted(set(reasons))),
                assessment=assessment,
            )
        )
    return tuple(sorted(blocks, key=lambda item: item.study_id))
