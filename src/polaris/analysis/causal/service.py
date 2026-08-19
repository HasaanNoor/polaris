"""Public service for explicit causal analysis."""

import hashlib
import json
from datetime import UTC, datetime

from polaris import __version__
from polaris.analysis.causal.diagnostics import (
    assumption_records,
    parallel_trends_diagnostic,
)
from polaris.analysis.causal.did import regression_did
from polaris.analysis.causal.event_study import estimate_event_study
from polaris.analysis.causal.models import (
    CAUSAL_RULESET_VERSION,
    CAUSAL_SCHEMA_VERSION,
    CausalAnalysisRequest,
    CausalAnalysisResult,
    CausalDesignDiagnostics,
    CausalEstimator,
    CausalMethod,
    CausalProvenance,
    CausalSampleSummary,
)
from polaris.analysis.causal.treatment import build_treatment_panel
from polaris.analysis.causal.validation import validate_causal_compatibility
from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisFindingCode,
    AnalysisSampleSummary,
    FindingSeverity,
    MissingDataPolicy,
)


def run_causal_analysis(*, request: CausalAnalysisRequest) -> CausalAnalysisResult:
    """Run an explicitly supplied and validated causal design."""

    ingestion = request.ingestion_result
    specification = request.causal_specification
    validate_causal_compatibility(ingestion, specification)
    panel = build_treatment_panel(ingestion, specification)
    limitations = _limitations(panel, specification)
    findings = _findings(panel, limitations)
    event_results = ()
    excluded_by_window = 0
    if specification.method is CausalMethod.DIFFERENCE_IN_DIFFERENCES:
        effect, regression = regression_did(
            panel,
            specification,
            confidence_level=request.effective_confidence_level,
            significance_threshold=request.significance_threshold,
        )
        estimator = CausalEstimator.TWFE_DID
    else:
        effect, regression, event_results, excluded_by_window = estimate_event_study(
            panel,
            specification,
            confidence_level=request.effective_confidence_level,
            significance_threshold=request.significance_threshold,
        )
        estimator = CausalEstimator.TWFE_EVENT_STUDY

    pre_periods = int(
        len(
            {
                float(row[specification.time_variable.variable_id])
                for row in panel.rows
                if specification.pre_treatment_window[0]
                <= float(row[specification.time_variable.variable_id])
                <= specification.pre_treatment_window[1]
            }
        )
    )
    diagnostic = parallel_trends_diagnostic(event_results, required_pre_periods=pre_periods)
    assumptions = assumption_records(diagnostic, limitations=limitations)
    timestamp = datetime.now(UTC)
    included_rows = tuple(
        sorted(
            int(row["_source_row_number"])
            for row in panel.rows
            if not (
                specification.method is CausalMethod.EVENT_STUDY
                and specification.event_study is not None
                and not (
                    specification.event_study.min_event_time
                    <= int(
                        float(row[specification.time_variable.variable_id])
                        - panel.treatment_start_period
                    )
                    <= specification.event_study.max_event_time
                )
            )
        )
    )
    excluded_rows = tuple(sorted(set(panel.excluded_row_numbers)))
    analysis_sample = AnalysisSampleSummary(
        required_variable_ids=(
            specification.entity_variable.variable_id,
            specification.time_variable.variable_id,
            specification.outcome_variable.variable_id,
            specification.treatment.treatment_variable.variable_id,
            *(item.variable_id for item in specification.covariates),
        ),
        sample_size=len(included_rows),
        included_row_numbers=included_rows,
        excluded_row_numbers=excluded_rows,
        exclusions=panel.sample.exclusions,
        missing_data_policy=MissingDataPolicy.COMPLETE_CASE,
    )
    sample_summary = CausalSampleSummary(
        input_rows=len(ingestion.normalized_records),
        included_rows=len(included_rows),
        excluded_rows=len(excluded_rows),
        treated_entity_count=len(panel.treated_entities),
        control_entity_count=len(panel.control_entities),
        cluster_count=len(panel.treated_entities) + len(panel.control_entities),
        pre_period_count=pre_periods,
        post_period_count=int(
            len(
                {
                    float(row[specification.time_variable.variable_id])
                    for row in panel.rows
                    if specification.post_treatment_window[0]
                    <= float(row[specification.time_variable.variable_id])
                    <= specification.post_treatment_window[1]
                }
            )
        ),
        event_window_excluded_rows=excluded_by_window,
        included_row_numbers=included_rows,
        excluded_row_numbers=excluded_rows,
    )
    provenance = CausalProvenance(
        dataset_id=ingestion.dataset_manifest.dataset_id,
        source_checksum_sha256=ingestion.checksum_sha256,
        ingestion_timestamp=ingestion.ingestion_timestamp,
        specification=specification,
        treatment_source=specification.treatment.treatment_source,
        treatment_assignment_variable=specification.treatment.treatment_variable.variable_id,
        treatment_timing_variable=(
            specification.treatment.treatment_timing_variable.variable_id
            if specification.treatment.treatment_timing_variable is not None
            else None
        ),
        entity_variable_id=specification.entity_variable.variable_id,
        time_variable_id=specification.time_variable.variable_id,
        outcome_variable_id=specification.outcome_variable.variable_id,
        covariate_ids=tuple(item.variable_id for item in specification.covariates),
        included_row_numbers=included_rows,
        excluded_row_numbers=excluded_rows,
        analysis_timestamp=timestamp,
        software_version=f"polaris-{__version__}",
    )
    return CausalAnalysisResult(
        causal_analysis_id=_causal_analysis_id(ingestion.checksum_sha256, specification),
        method=specification.method,
        estimator=estimator,
        causal_specification=specification,
        dataset_id=ingestion.dataset_manifest.dataset_id,
        source_checksum_sha256=ingestion.checksum_sha256,
        estimand=specification.estimand,
        treatment_effect=effect,
        regression_result=regression,
        sample_summary=sample_summary,
        analysis_sample=analysis_sample,
        event_study_results=event_results,
        assumptions=assumptions,
        diagnostics=CausalDesignDiagnostics(
            structural_validation_passed=True,
            treatment_integrity_passed=True,
            parallel_trends=diagnostic,
            warnings=tuple(findings),
        ),
        limitations=limitations,
        findings=tuple(findings),
        provenance=provenance,
        analysis_timestamp=timestamp,
        software_version=f"polaris-{__version__}",
    )


def _limitations(panel, specification) -> tuple[str, ...]:
    values = [
        "causal language is conditional on the supplied design and identifying assumptions",
        "Phase 22 does not support staggered-adoption causal estimators",
    ]
    if len(panel.treated_entities) < 3:
        values.append("very few treated entities limit causal-design credibility")
    if len(panel.treated_entities) + len(panel.control_entities) < 20:
        values.append("low cluster count; entity-clustered uncertainty may be unreliable")
    acknowledged = set(specification.acknowledged_post_treatment_covariates)
    for covariate in specification.covariates:
        if covariate.variable_id not in acknowledged and specification.strict_covariate_timing:
            values.append(
                f'covariate "{covariate.variable_id}" may be post-treatment; '
                "bad controls can bias causal estimates"
            )
    return tuple(sorted(set(values)))


def _findings(panel, limitations: tuple[str, ...]) -> tuple[AnalysisFinding, ...]:
    findings = []
    cluster_count = len(panel.treated_entities) + len(panel.control_entities)
    if cluster_count < 20:
        findings.append(
            AnalysisFinding(
                severity=FindingSeverity.WARNING,
                code=AnalysisFindingCode.LOW_CLUSTER_COUNT,
                message=(
                    f"causal analysis uses {cluster_count} entity clusters; small-cluster "
                    "standard errors can be unreliable"
                ),
                method="causal_design",
                statistic=float(cluster_count),
                threshold=20.0,
            )
        )
    for limitation in limitations:
        if "post-treatment" in limitation:
            findings.append(
                AnalysisFinding(
                    severity=FindingSeverity.WARNING,
                    code=AnalysisFindingCode.CAUSAL_INTERPRETATION_UNSUPPORTED,
                    message=limitation,
                    method="causal_design",
                )
            )
    return tuple(findings)


def _causal_analysis_id(checksum: str, specification) -> str:
    payload = {
        "checksum_sha256": checksum,
        "specification": json.loads(specification.model_dump_json()),
        "schema_version": CAUSAL_SCHEMA_VERSION,
        "ruleset_version": CAUSAL_RULESET_VERSION,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "causal_analysis_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
