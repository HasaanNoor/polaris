"""Deterministic evidence extraction from Phase 4 analysis results."""

from collections import Counter
from datetime import datetime

from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisResult,
    CorrelationAnalysisResult,
    DescriptiveAnalysisResult,
    OLSRegressionResult,
    PanelRegressionResult,
)
from polaris.evidence.limitations import (
    limitations_from_diagnostic,
    limitations_from_findings,
    ordered_limitations,
)
from polaris.evidence.models import (
    AnalysisWarningEvidenceRecord,
    CorrelationEvidenceRecord,
    DescriptiveEvidenceRecord,
    DiagnosticEvidenceRecord,
    Direction,
    EvidenceRecord,
    EvidenceType,
    LimitationCode,
    ModelFitEvidenceRecord,
    RegressionCoefficientEvidenceRecord,
    SampleQualityEvidenceRecord,
)
from polaris.evidence.provenance import evidence_id, evidence_provenance


def extract_evidence_records(
    analysis_result: AnalysisResult,
    *,
    extraction_timestamp: datetime | None = None,
) -> tuple[EvidenceRecord, ...]:
    provenance = evidence_provenance(analysis_result, extraction_timestamp=extraction_timestamp)
    records: list[EvidenceRecord] = [
        _sample_quality_evidence(analysis_result, provenance),
        *[
            _warning_evidence(analysis_result, finding, provenance)
            for finding in analysis_result.findings
        ],
    ]

    method_result = analysis_result.method_result
    if isinstance(method_result, DescriptiveAnalysisResult):
        records.extend(_descriptive_evidence(analysis_result, method_result, provenance))
    elif isinstance(method_result, CorrelationAnalysisResult):
        records.extend(_correlation_evidence(analysis_result, method_result, provenance))
    elif isinstance(method_result, OLSRegressionResult | PanelRegressionResult):
        records.extend(_regression_evidence(analysis_result, method_result, provenance))

    records.extend(
        _diagnostic_evidence(analysis_result, diagnostic, provenance)
        for diagnostic in analysis_result.diagnostics
    )
    return tuple(sorted(records, key=lambda record: record.evidence_id))


def direction_from_number(value: float | None) -> Direction:
    if value is None:
        return Direction.UNDEFINED
    if value > 0:
        return Direction.POSITIVE
    if value < 0:
        return Direction.NEGATIVE
    return Direction.ZERO


def _descriptive_evidence(analysis_result, method_result, provenance):
    records: list[DescriptiveEvidenceRecord] = []
    for summary in method_result.variables:
        limitations = limitations_from_findings(summary.findings)
        flags = tuple(finding.code for finding in summary.findings)
        if summary.numeric is not None:
            payload = _identity_payload(
                analysis_result,
                EvidenceType.DESCRIPTIVE_SUMMARY,
                variable_id=summary.variable_id,
                summary_kind="numeric",
            )
            numeric = summary.numeric
            records.append(
                DescriptiveEvidenceRecord(
                    evidence_id=evidence_id(payload),
                    source_analysis_result_id=analysis_result.result_id,
                    dataset_id=analysis_result.dataset_id,
                    source_checksum_sha256=analysis_result.source_checksum_sha256,
                    statistical_procedure=analysis_result.analysis_method,
                    sample_size=analysis_result.analysis_sample.sample_size,
                    diagnostic_flags=flags,
                    limitation_codes=limitations,
                    provenance=provenance,
                    variable_id=summary.variable_id,
                    variable_type=summary.variable_type,
                    summary_kind="numeric",
                    count=numeric.count,
                    missing_count=numeric.missing_count,
                    mean=numeric.mean,
                    standard_deviation=numeric.standard_deviation,
                    minimum=numeric.minimum,
                    percentile_25=numeric.percentile_25,
                    median=numeric.median,
                    percentile_75=numeric.percentile_75,
                    maximum=numeric.maximum,
                )
            )
        if summary.categorical is not None:
            payload = _identity_payload(
                analysis_result,
                EvidenceType.DESCRIPTIVE_SUMMARY,
                variable_id=summary.variable_id,
                summary_kind="categorical",
            )
            categorical = summary.categorical
            records.append(
                DescriptiveEvidenceRecord(
                    evidence_id=evidence_id(payload),
                    source_analysis_result_id=analysis_result.result_id,
                    dataset_id=analysis_result.dataset_id,
                    source_checksum_sha256=analysis_result.source_checksum_sha256,
                    statistical_procedure=analysis_result.analysis_method,
                    sample_size=analysis_result.analysis_sample.sample_size,
                    diagnostic_flags=flags,
                    limitation_codes=limitations,
                    provenance=provenance,
                    variable_id=summary.variable_id,
                    variable_type=summary.variable_type,
                    summary_kind="categorical",
                    count=categorical.count,
                    missing_count=categorical.missing_count,
                    unique_count=categorical.unique_count,
                    most_frequent_value=categorical.most_frequent_value,
                    most_frequent_value_count=categorical.most_frequent_value_count,
                )
            )
    return records


def _correlation_evidence(analysis_result, method_result, provenance):
    records: list[CorrelationEvidenceRecord] = []
    for pair in method_result.pairs:
        limitations = limitations_from_findings(pair.warnings)
        flags = tuple(warning.code for warning in pair.warnings)
        payload = _identity_payload(
            analysis_result,
            EvidenceType.CORRELATION,
            variable_id_1=pair.variable_id_1,
            variable_id_2=pair.variable_id_2,
            method=pair.method,
        )
        records.append(
            CorrelationEvidenceRecord(
                evidence_id=evidence_id(payload),
                source_analysis_result_id=analysis_result.result_id,
                dataset_id=analysis_result.dataset_id,
                source_checksum_sha256=analysis_result.source_checksum_sha256,
                statistical_procedure=analysis_result.analysis_method,
                sample_size=pair.observation_count,
                diagnostic_flags=flags,
                limitation_codes=limitations,
                provenance=provenance,
                variable_id_1=pair.variable_id_1,
                variable_id_2=pair.variable_id_2,
                method=pair.method,
                correlation_coefficient=pair.correlation_coefficient,
                p_value=pair.p_value,
                observation_count=pair.observation_count,
                defined=pair.defined,
                direction=direction_from_number(pair.correlation_coefficient)
                if pair.defined
                else Direction.UNDEFINED,
                excluded_row_numbers=tuple(sorted(pair.excluded_row_numbers)),
                missing_exclusion_count=len(pair.excluded_row_numbers),
            )
        )
    return records


def _regression_evidence(analysis_result, method_result, provenance):
    records: list[EvidenceRecord] = []
    model_limitations = limitations_from_findings(method_result.warnings)
    model_flags = tuple(warning.code for warning in method_result.warnings)
    fit_payload = _identity_payload(
        analysis_result,
        EvidenceType.MODEL_FIT,
        dependent_variable_id=method_result.dependent_variable_id,
        model_result_id=analysis_result.result_id,
    )
    records.append(
        ModelFitEvidenceRecord(
            evidence_id=evidence_id(fit_payload),
            source_analysis_result_id=analysis_result.result_id,
            dataset_id=analysis_result.dataset_id,
            source_checksum_sha256=analysis_result.source_checksum_sha256,
            statistical_procedure=analysis_result.analysis_method,
            sample_size=method_result.sample_size,
            diagnostic_flags=model_flags,
            limitation_codes=model_limitations,
            provenance=provenance,
            dependent_variable_id=method_result.dependent_variable_id,
            predictor_variable_ids=tuple(sorted(method_result.predictor_variable_ids)),
            r_squared=getattr(method_result, "r_squared", None)
            if isinstance(method_result, OLSRegressionResult)
            else method_result.fit.within_r_squared,
            adjusted_r_squared=getattr(method_result, "adjusted_r_squared", None)
            if isinstance(method_result, OLSRegressionResult)
            else method_result.fit.adjusted_within_r_squared,
            residual_degrees_of_freedom=method_result.residual_degrees_of_freedom,
            model_degrees_of_freedom=method_result.model_degrees_of_freedom,
            residual_sum_of_squares=method_result.residual_sum_of_squares,
            mean_squared_error=method_result.mean_squared_error,
            model_result_id=analysis_result.result_id,
        )
    )
    for coefficient in method_result.coefficients:
        payload = _identity_payload(
            analysis_result,
            EvidenceType.REGRESSION_COEFFICIENT,
            dependent_variable_id=method_result.dependent_variable_id,
            term=coefficient.term,
            variable_id=coefficient.variable_id,
            model_result_id=analysis_result.result_id,
        )
        records.append(
            RegressionCoefficientEvidenceRecord(
                evidence_id=evidence_id(payload),
                source_analysis_result_id=analysis_result.result_id,
                dataset_id=analysis_result.dataset_id,
                source_checksum_sha256=analysis_result.source_checksum_sha256,
                statistical_procedure=analysis_result.analysis_method,
                sample_size=method_result.sample_size,
                diagnostic_flags=model_flags,
                limitation_codes=model_limitations,
                provenance=provenance,
                dependent_variable_id=method_result.dependent_variable_id,
                term=coefficient.term,
                variable_id=coefficient.variable_id,
                estimate=coefficient.estimate,
                standard_error=coefficient.standard_error,
                test_statistic=coefficient.test_statistic,
                p_value=coefficient.p_value,
                confidence_interval_low=coefficient.confidence_interval_low,
                confidence_interval_high=coefficient.confidence_interval_high,
                below_significance_threshold=coefficient.below_significance_threshold,
                direction=direction_from_number(coefficient.estimate),
                is_intercept=coefficient.variable_id is None,
                model_result_id=analysis_result.result_id,
                predictor_variable_ids=tuple(sorted(method_result.predictor_variable_ids)),
            )
        )
    for warning in method_result.warnings:
        records.append(_warning_evidence(analysis_result, warning, provenance))
    return records


def _diagnostic_evidence(analysis_result, diagnostic, provenance):
    payload = _identity_payload(
        analysis_result,
        EvidenceType.MODEL_DIAGNOSTIC,
        diagnostic_type=diagnostic.name,
        variable_id=diagnostic.variable_id,
    )
    return DiagnosticEvidenceRecord(
        evidence_id=evidence_id(payload),
        source_analysis_result_id=analysis_result.result_id,
        dataset_id=analysis_result.dataset_id,
        source_checksum_sha256=analysis_result.source_checksum_sha256,
        statistical_procedure=analysis_result.analysis_method,
        sample_size=analysis_result.analysis_sample.sample_size,
        diagnostic_flags=diagnostic.warning_codes,
        limitation_codes=limitations_from_diagnostic(diagnostic),
        provenance=provenance,
        diagnostic_type=diagnostic.name,
        status=diagnostic.status.value,
        statistic=diagnostic.statistic,
        p_value=diagnostic.p_value,
        variable_id=diagnostic.variable_id,
        warning_codes=diagnostic.warning_codes,
    )


def _sample_quality_evidence(analysis_result: AnalysisResult, provenance):
    sample = analysis_result.analysis_sample
    reasons = Counter(exclusion.reason for exclusion in sample.exclusions)
    total = sample.sample_size + len(sample.exclusions)
    percent = None if total == 0 else sample.sample_size / total * 100.0
    limitations = ()
    if sample.exclusions:
        limitations = (LimitationCode.MISSING_DATA_EXCLUSION,)
    payload = _identity_payload(
        analysis_result,
        EvidenceType.SAMPLE_QUALITY,
        required_variable_ids=tuple(sorted(sample.required_variable_ids)),
    )
    return SampleQualityEvidenceRecord(
        evidence_id=evidence_id(payload),
        source_analysis_result_id=analysis_result.result_id,
        dataset_id=analysis_result.dataset_id,
        source_checksum_sha256=analysis_result.source_checksum_sha256,
        statistical_procedure=analysis_result.analysis_method,
        sample_size=sample.sample_size,
        limitation_codes=limitations,
        provenance=provenance,
        required_variable_ids=tuple(sorted(sample.required_variable_ids)),
        original_accepted_record_count=total,
        final_analysis_sample_size=sample.sample_size,
        excluded_row_count=len(sample.exclusions),
        exclusion_reason_counts=tuple(sorted(reasons.items())),
        missing_value_exclusion_count=len(sample.exclusions),
        accepted_records_used_percentage=percent,
        included_row_numbers=tuple(sorted(sample.included_row_numbers)),
        excluded_row_numbers=tuple(sorted(sample.excluded_row_numbers)),
    )


def _warning_evidence(
    analysis_result: AnalysisResult,
    finding: AnalysisFinding,
    provenance,
) -> AnalysisWarningEvidenceRecord:
    payload = _identity_payload(
        analysis_result,
        EvidenceType.ANALYSIS_WARNING,
        finding_code=finding.code,
        variable_ids=tuple(sorted(finding.variable_ids)),
        method=finding.method,
        source_row_numbers=tuple(sorted(finding.source_row_numbers)),
    )
    return AnalysisWarningEvidenceRecord(
        evidence_id=evidence_id(payload),
        source_analysis_result_id=analysis_result.result_id,
        dataset_id=analysis_result.dataset_id,
        source_checksum_sha256=analysis_result.source_checksum_sha256,
        statistical_procedure=analysis_result.analysis_method,
        sample_size=analysis_result.analysis_sample.sample_size,
        diagnostic_flags=(finding.code,),
        limitation_codes=limitations_from_findings((finding,)),
        provenance=provenance,
        finding_code=finding.code,
        severity=finding.severity.value,
        variable_ids=tuple(sorted(finding.variable_ids)),
        method=finding.method,
        statistic=finding.statistic,
        threshold=finding.threshold,
        source_row_numbers=tuple(sorted(finding.source_row_numbers)),
    )


def merge_limitations(*groups: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
    return ordered_limitations(item for group in groups for item in group)


def _identity_payload(
    analysis_result: AnalysisResult,
    evidence_type: EvidenceType,
    **extra,
) -> dict[str, object]:
    return {
        "source_analysis_result_id": analysis_result.result_id,
        "evidence_type": evidence_type,
        "statistical_procedure": analysis_result.analysis_method,
        **extra,
    }
