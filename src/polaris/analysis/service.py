"""Public orchestration entry point for deterministic statistical analysis."""

import hashlib
import json
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version

from polaris import __version__
from polaris.analysis.compatibility import (
    resolve_procedure,
    validate_compatibility,
)
from polaris.analysis.correlation import correlate_variables
from polaris.analysis.descriptive import describe_variables
from polaris.analysis.diagnostics import ols_diagnostics
from polaris.analysis.errors import AnalysisNotReadyError, UnsupportedAnalysisMethodError
from polaris.analysis.models import (
    ANALYSIS_SCHEMA_VERSION,
    AnalysisProvenance,
    AnalysisRequest,
    AnalysisResult,
    AnalysisSampleSummary,
)
from polaris.analysis.panel_compatibility import (
    is_panel_procedure,
    validate_panel_compatibility,
)
from polaris.analysis.panel_models import fit_panel_regression
from polaris.analysis.panel_sample import build_panel_sample
from polaris.analysis.regression import fit_ols
from polaris.analysis.sample import build_analysis_sample
from polaris.schemas.common import StatisticalProcedure


def run_analysis(*, request: AnalysisRequest) -> AnalysisResult:
    ingestion = request.ingestion_result
    if not ingestion.validation_report.analysis_ready:
        raise AnalysisNotReadyError(
            "analysis requires an analysis-ready ingestion result",
            dataset_id=ingestion.dataset_manifest.dataset_id,
        )
    specification = request.statistical_specification
    procedure = resolve_procedure(specification)
    predictor_ids: tuple[str, ...] = ()
    if is_panel_procedure(procedure):
        variable_ids, predictor_ids, compatibility_findings = validate_panel_compatibility(
            ingestion, specification, procedure
        )
        entity_id = specification.entity_variable.variable_id  # type: ignore[union-attr]
        time_id = specification.time_variable.variable_id  # type: ignore[union-attr]
        sample, lag_operations, sample_findings = build_panel_sample(
            ingestion,
            variable_ids=tuple(
                dict.fromkeys(
                    (
                        specification.outcome_variable.variable_id,
                        *(
                            variable.variable_id
                            for variable in (
                                *specification.exposure_variables,
                                *specification.covariates,
                            )
                        ),
                        *(lag.source_variable.variable_id for lag in specification.lags),
                    )
                )
            ),
            entity_variable_id=entity_id,
            time_variable_id=time_id,
            lags=tuple(specification.lags),
        )
    else:
        variable_ids, compatibility_findings = validate_compatibility(
            ingestion, specification, procedure
        )
        sample, sample_findings = build_analysis_sample(ingestion, variable_ids)

    diagnostics = ()
    if procedure is StatisticalProcedure.DESCRIPTIVE_STATISTICS:
        method_result = describe_variables(ingestion, variable_ids)
    elif procedure is StatisticalProcedure.PEARSON_CORRELATION:
        method_result = correlate_variables(ingestion, variable_ids, method="pearson")
    elif procedure is StatisticalProcedure.SPEARMAN_CORRELATION:
        method_result = correlate_variables(ingestion, variable_ids, method="spearman")
    elif procedure is StatisticalProcedure.ORDINARY_LEAST_SQUARES:
        predictor_ids = tuple(
            variable.variable_id
            for variable in (*specification.exposure_variables, *specification.covariates)
        )
        method_result = fit_ols(
            sample,
            dependent_variable_id=specification.outcome_variable.variable_id,
            predictor_variable_ids=predictor_ids,
            include_intercept=request.execution_settings.include_intercept,
            confidence_level=request.effective_confidence_level,
            significance_threshold=request.significance_threshold,
        )
        diagnostics = ols_diagnostics(sample, method_result)
    elif is_panel_procedure(procedure):
        method_result = fit_panel_regression(
            sample,
            procedure=procedure,
            dependent_variable_id=specification.outcome_variable.variable_id,
            predictor_variable_ids=predictor_ids,
            entity_variable_id=specification.entity_variable.variable_id,  # type: ignore[union-attr]
            time_variable_id=specification.time_variable.variable_id,  # type: ignore[union-attr]
            standard_error_strategy=specification.standard_error_strategy,
            lag_operations=lag_operations,
            confidence_level=request.effective_confidence_level,
            significance_threshold=request.significance_threshold,
        )
        diagnostics = (
            *diagnostics,
            *(
                diagnostic
                for diagnostic in (
                    _panel_condition_diagnostic(method_result.transformed_condition_number),
                )
            ),
        )
    else:
        raise UnsupportedAnalysisMethodError(
            f'unsupported analysis procedure "{procedure.value}"',
            dataset_id=ingestion.dataset_manifest.dataset_id,
            method=procedure.value,
        )

    timestamp = datetime.now(UTC)
    sample_summary = AnalysisSampleSummary(
        required_variable_ids=variable_ids,
        sample_size=sample.sample_size,
        included_row_numbers=sample.included_row_numbers,
        excluded_row_numbers=tuple(exclusion.row_number for exclusion in sample.exclusions),
        exclusions=sample.exclusions,
        missing_data_policy=request.execution_settings.missing_data_policy,
    )
    provenance = AnalysisProvenance(
        dataset_id=ingestion.dataset_manifest.dataset_id,
        source_checksum_sha256=ingestion.checksum_sha256,
        ingestion_timestamp=ingestion.ingestion_timestamp,
        specification=specification,
        included_row_numbers=sample.included_row_numbers,
        excluded_row_numbers=sample_summary.excluded_row_numbers,
        analysis_timestamp=timestamp,
        library_versions=_library_versions(),
        software_version=f"polaris-{__version__}",
        execution_settings=request.execution_settings,
    )
    return AnalysisResult(
        result_id=_result_id(ingestion.checksum_sha256, specification, procedure),
        analysis_method=procedure,
        statistical_specification=specification,
        dataset_id=ingestion.dataset_manifest.dataset_id,
        source_checksum_sha256=ingestion.checksum_sha256,
        analysis_sample=sample_summary,
        method_result=method_result,
        diagnostics=diagnostics,
        findings=tuple((*compatibility_findings, *sample_findings)),
        analysis_timestamp=timestamp,
        software_version=f"polaris-{__version__}",
        provenance=provenance,
    )


def _result_id(
    checksum: str,
    specification: object,
    procedure: StatisticalProcedure,
) -> str:
    payload = {
        "checksum_sha256": checksum,
        "procedure": procedure.value,
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "specification": json.loads(specification.model_dump_json()),  # type: ignore[attr-defined]
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "analysis_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _library_versions() -> tuple[str, ...]:
    libraries = ["numpy", "scipy", "pydantic"]
    values: list[str] = []
    for library in libraries:
        try:
            values.append(f"{library}-{version(library)}")
        except PackageNotFoundError:
            values.append(f"{library}-unknown")
    return tuple(values)


def _panel_condition_diagnostic(condition_number: float | None):
    from polaris.analysis.models import AnalysisFindingCode, DiagnosticResult, DiagnosticStatus

    return DiagnosticResult(
        name="transformed_condition_number",
        status=DiagnosticStatus.CALCULATED
        if condition_number is not None
        else DiagnosticStatus.UNDEFINED,
        statistic=condition_number,
        warning_codes=()
        if condition_number is not None
        else (AnalysisFindingCode.UNDEFINED_STATISTIC,),
        explanation="Condition number was calculated from the transformed panel design matrix.",
    )
