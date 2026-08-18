"""Fixed-effects panel regression for deterministic country-year analysis."""

from collections import Counter

import numpy as np
from scipy import stats

from polaris.analysis.errors import (
    InsufficientClustersError,
    InsufficientPanelDataError,
    PanelRankDeficiencyError,
    TimeInvariantPredictorError,
)
from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisFindingCode,
    AnalysisSample,
    FindingSeverity,
    PanelClusterConfig,
    PanelFitMetrics,
    PanelFixedEffectsConfig,
    PanelLagOperation,
    PanelRegressionResult,
    PanelSampleSummary,
    PanelVariableVariation,
    RegressionCoefficient,
    RegressionSummary,
)
from polaris.analysis.utils import safe_float, summarize
from polaris.schemas.common import StatisticalProcedure
from polaris.schemas.statistics import StandardErrorSpec

LOW_CLUSTER_WARNING_THRESHOLD = 20
LOW_WITHIN_VARIATION_RATIO = 0.01


def fit_panel_regression(
    sample: AnalysisSample,
    *,
    procedure: StatisticalProcedure,
    dependent_variable_id: str,
    predictor_variable_ids: tuple[str, ...],
    entity_variable_id: str,
    time_variable_id: str,
    standard_error_strategy: StandardErrorSpec | None,
    lag_operations: tuple[PanelLagOperation, ...],
    confidence_level: float,
    significance_threshold: float | None,
) -> PanelRegressionResult:
    entity_fe = procedure in {
        StatisticalProcedure.PANEL_ENTITY_FE,
        StatisticalProcedure.PANEL_TWO_WAY_FE,
    }
    time_fe = procedure is StatisticalProcedure.PANEL_TWO_WAY_FE
    if procedure is StatisticalProcedure.FIRST_DIFFERENCE:
        return _fit_first_difference(
            sample,
            dependent_variable_id=dependent_variable_id,
            predictor_variable_ids=predictor_variable_ids,
            entity_variable_id=entity_variable_id,
            time_variable_id=time_variable_id,
            standard_error_strategy=standard_error_strategy,
            lag_operations=lag_operations,
            confidence_level=confidence_level,
            significance_threshold=significance_threshold,
        )
    return _fit_fixed_effects(
        sample,
        procedure=procedure,
        dependent_variable_id=dependent_variable_id,
        predictor_variable_ids=predictor_variable_ids,
        entity_variable_id=entity_variable_id,
        time_variable_id=time_variable_id,
        entity_fe=entity_fe,
        time_fe=time_fe,
        standard_error_strategy=standard_error_strategy,
        lag_operations=lag_operations,
        confidence_level=confidence_level,
        significance_threshold=significance_threshold,
    )


def _fit_fixed_effects(
    sample: AnalysisSample,
    *,
    procedure: StatisticalProcedure,
    dependent_variable_id: str,
    predictor_variable_ids: tuple[str, ...],
    entity_variable_id: str,
    time_variable_id: str,
    entity_fe: bool,
    time_fe: bool,
    standard_error_strategy: StandardErrorSpec | None,
    lag_operations: tuple[PanelLagOperation, ...],
    confidence_level: float,
    significance_threshold: float | None,
) -> PanelRegressionResult:
    y = np.asarray([row[dependent_variable_id] for row in sample.rows], dtype=float)
    x = np.asarray(
        [[row[variable_id] for variable_id in predictor_variable_ids] for row in sample.rows],
        dtype=float,
    )
    entities = tuple(str(row[entity_variable_id]) for row in sample.rows)
    times = tuple(float(row[time_variable_id]) for row in sample.rows)
    _require_panel_depth(entities)
    transformed_y = y.copy()
    transformed_x = x.copy()
    if entity_fe and time_fe:
        transformed_y = _twoway_demean(transformed_y, entities, times)
        transformed_x = _twoway_demean_matrix(transformed_x, entities, times)
    elif entity_fe:
        transformed_y = _demean_by(transformed_y, entities)
        transformed_x = _demean_matrix_by(transformed_x, entities)
    elif time_fe:
        transformed_y = _demean_by(transformed_y, times)
        transformed_x = _demean_matrix_by(transformed_x, times)

    _reject_time_invariant_predictors(transformed_x, predictor_variable_ids)
    rank = int(np.linalg.matrix_rank(transformed_x))
    if rank < transformed_x.shape[1]:
        raise PanelRankDeficiencyError("transformed panel design matrix is rank deficient")
    beta = np.linalg.pinv(transformed_x) @ transformed_y
    fitted_transformed = transformed_x @ beta
    residuals = transformed_y - fitted_transformed
    nobs = int(y.size)
    parameter_count = int(transformed_x.shape[1])
    absorbed_df = _absorbed_degrees_of_freedom(
        entities, times, entity_fe=entity_fe, time_fe=time_fe
    )
    residual_df = float(nobs - parameter_count - absorbed_df)
    if residual_df <= 0:
        raise InsufficientPanelDataError("panel regression has no residual degrees of freedom")
    rss = safe_float(np.sum(residuals**2))
    mse = safe_float((rss or 0.0) / residual_df) if rss is not None else None
    covariance, cluster_config, warnings = _cluster_covariance(
        transformed_x,
        residuals,
        entities=entities,
        standard_error_strategy=standard_error_strategy,
        residual_df=residual_df,
    )
    coefficients = _panel_coefficients(
        beta,
        covariance,
        residual_df=residual_df,
        predictor_variable_ids=predictor_variable_ids,
        confidence_level=confidence_level,
        significance_threshold=significance_threshold,
        cluster_count=cluster_config.cluster_count,
    )
    panel_sample = _panel_sample_summary(
        sample,
        entities=entities,
        times=times,
        cluster_count=cluster_config.cluster_count,
        lag_exclusions=sum(lag.rows_lost for lag in lag_operations),
    )
    warnings.extend(_panel_warnings(panel_sample))
    variation = _variation(
        sample, (dependent_variable_id, *predictor_variable_ids), entity_variable_id
    )
    warnings.extend(_variation_warnings(variation))
    fit = _fit_metrics(
        y=y,
        x=x,
        beta=beta,
        entities=entities,
        transformed_y=transformed_y,
        residuals=residuals,
        residual_df=residual_df,
        parameter_count=parameter_count,
    )
    return PanelRegressionResult(
        procedure=procedure,
        dependent_variable_id=dependent_variable_id,
        predictor_variable_ids=predictor_variable_ids,
        sample_size=nobs,
        coefficients=coefficients,
        fixed_effects=PanelFixedEffectsConfig(
            entity_variable_id=entity_variable_id,
            time_variable_id=time_variable_id,
            entity_fixed_effects=entity_fe,
            time_fixed_effects=time_fe,
            intercept_reported=False,
            intercept_explanation=(
                "Fixed-effects models are estimated on transformed data; Polaris does not "
                "report an intercept because it is not substantively interpretable."
            ),
        ),
        cluster=cluster_config,
        panel_sample=panel_sample,
        lag_operations=lag_operations,
        variation=variation,
        fit=fit,
        residual_degrees_of_freedom=residual_df,
        model_degrees_of_freedom=float(parameter_count),
        residual_sum_of_squares=rss,
        mean_squared_error=mse,
        fitted_value_summary=_regression_summary(fitted_transformed),
        residual_summary=_regression_summary(residuals),
        transformed_condition_number=safe_float(np.linalg.cond(transformed_x)),
        warnings=tuple(warnings),
    )


def _fit_first_difference(
    sample: AnalysisSample,
    *,
    dependent_variable_id: str,
    predictor_variable_ids: tuple[str, ...],
    entity_variable_id: str,
    time_variable_id: str,
    standard_error_strategy: StandardErrorSpec | None,
    lag_operations: tuple[PanelLagOperation, ...],
    confidence_level: float,
    significance_threshold: float | None,
) -> PanelRegressionResult:
    rows: list[dict[str, float | str]] = []
    for _, group_rows in _rows_by_entity(sample.rows, entity_variable_id).items():
        ordered = sorted(
            group_rows, key=lambda row: (float(row[time_variable_id]), str(row[entity_variable_id]))
        )
        by_time = {float(row[time_variable_id]): row for row in ordered}
        for row in ordered:
            previous = by_time.get(float(row[time_variable_id]) - 1)
            if previous is None:
                continue
            diff_row: dict[str, float | str] = {
                entity_variable_id: str(row[entity_variable_id]),
                time_variable_id: float(row[time_variable_id]),
                dependent_variable_id: float(row[dependent_variable_id])
                - float(previous[dependent_variable_id]),
            }
            for variable_id in predictor_variable_ids:
                diff_row[variable_id] = float(row[variable_id]) - float(previous[variable_id])
            rows.append(diff_row)
    if len(rows) <= len(predictor_variable_ids) + 2:
        raise InsufficientPanelDataError("first-difference analysis requires consecutive periods")
    diff_sample = AnalysisSample(
        variable_ids=(
            dependent_variable_id,
            *predictor_variable_ids,
            entity_variable_id,
            time_variable_id,
        ),
        rows=tuple(rows),  # type: ignore[arg-type]
        included_row_numbers=sample.included_row_numbers,
        included_source_line_numbers=sample.included_source_line_numbers,
        exclusions=sample.exclusions,
    )
    return _fit_fixed_effects(
        diff_sample,
        procedure=StatisticalProcedure.FIRST_DIFFERENCE,
        dependent_variable_id=dependent_variable_id,
        predictor_variable_ids=predictor_variable_ids,
        entity_variable_id=entity_variable_id,
        time_variable_id=time_variable_id,
        entity_fe=False,
        time_fe=False,
        standard_error_strategy=standard_error_strategy,
        lag_operations=lag_operations,
        confidence_level=confidence_level,
        significance_threshold=significance_threshold,
    )


def _demean_by(values: np.ndarray, groups: tuple[object, ...]) -> np.ndarray:
    output = values.astype(float).copy()
    for group in sorted(set(groups), key=str):
        mask = np.asarray([item == group for item in groups])
        output[mask] = values[mask] - np.mean(values[mask])
    return output


def _demean_matrix_by(values: np.ndarray, groups: tuple[object, ...]) -> np.ndarray:
    return np.column_stack(
        [_demean_by(values[:, index], groups) for index in range(values.shape[1])]
    )


def _twoway_demean(
    values: np.ndarray,
    entities: tuple[object, ...],
    times: tuple[object, ...],
) -> np.ndarray:
    output = values.astype(float).copy()
    overall = float(np.mean(values))
    entity_means = {
        entity: float(np.mean(values[np.asarray([item == entity for item in entities])]))
        for entity in sorted(set(entities), key=str)
    }
    time_means = {
        time: float(np.mean(values[np.asarray([item == time for item in times])]))
        for time in sorted(set(times), key=str)
    }
    for index, value in enumerate(values):
        output[index] = value - entity_means[entities[index]] - time_means[times[index]] + overall
    return output


def _twoway_demean_matrix(
    values: np.ndarray,
    entities: tuple[object, ...],
    times: tuple[object, ...],
) -> np.ndarray:
    return np.column_stack(
        [_twoway_demean(values[:, index], entities, times) for index in range(values.shape[1])]
    )


def _require_panel_depth(entities: tuple[str, ...]) -> None:
    counts = Counter(entities)
    repeated = [entity for entity, count in counts.items() if count >= 2]
    if len(repeated) < 2:
        raise InsufficientPanelDataError(
            "panel analysis requires repeated observations for at least two entities"
        )


def _reject_time_invariant_predictors(
    x: np.ndarray, predictor_variable_ids: tuple[str, ...]
) -> None:
    for index, variable_id in enumerate(predictor_variable_ids):
        if float(np.var(x[:, index])) <= 1e-12:
            raise TimeInvariantPredictorError(
                f'predictor "{variable_id}" has no estimable within-entity variation',
                variable_id=variable_id,
            )


def _absorbed_degrees_of_freedom(
    entities: tuple[str, ...],
    times: tuple[float, ...],
    *,
    entity_fe: bool,
    time_fe: bool,
) -> int:
    absorbed = 0
    if entity_fe:
        absorbed += max(0, len(set(entities)) - 1)
    if time_fe:
        absorbed += max(0, len(set(times)) - 1)
    return absorbed


def _cluster_covariance(
    x: np.ndarray,
    residuals: np.ndarray,
    *,
    entities: tuple[str, ...],
    standard_error_strategy: StandardErrorSpec | None,
    residual_df: float,
) -> tuple[np.ndarray, PanelClusterConfig, list[AnalysisFinding]]:
    cluster_variable = None
    if standard_error_strategy is not None and standard_error_strategy.cluster_variables:
        cluster_variable = standard_error_strategy.cluster_variables[0].variable_id
    clusters = entities
    cluster_count = len(set(clusters))
    if cluster_count < 2:
        raise InsufficientClustersError(
            "cluster-robust standard errors require at least two clusters"
        )
    xpx_inv = np.linalg.pinv(x.T @ x)
    meat = np.zeros((x.shape[1], x.shape[1]))
    for cluster in sorted(set(clusters)):
        mask = np.asarray([item == cluster for item in clusters])
        xg = x[mask, :]
        ug = residuals[mask]
        score = xg.T @ ug
        meat += np.outer(score, score)
    nobs = x.shape[0]
    parameters = x.shape[1]
    correction = (cluster_count / (cluster_count - 1)) * ((nobs - 1) / max(1, nobs - parameters))
    covariance = correction * (xpx_inv @ meat @ xpx_inv)
    warnings: list[AnalysisFinding] = []
    warning = None
    if cluster_count < LOW_CLUSTER_WARNING_THRESHOLD:
        warning = (
            f"clustered inference uses {cluster_count} entity clusters; small-cluster "
            "standard errors can be unreliable"
        )
        warnings.append(
            AnalysisFinding(
                severity=FindingSeverity.WARNING,
                code=AnalysisFindingCode.LOW_CLUSTER_COUNT,
                message=warning,
                method="cluster_robust_entity",
                statistic=float(cluster_count),
                threshold=float(LOW_CLUSTER_WARNING_THRESHOLD),
            )
        )
    if residual_df <= 0:
        raise InsufficientPanelDataError("panel regression has no residual degrees of freedom")
    return (
        covariance,
        PanelClusterConfig(
            strategy="cluster_robust_entity",
            cluster_variable_id=cluster_variable,
            cluster_count=cluster_count,
            warning=warning,
        ),
        warnings,
    )


def _panel_coefficients(
    beta: np.ndarray,
    covariance: np.ndarray,
    *,
    residual_df: float,
    predictor_variable_ids: tuple[str, ...],
    confidence_level: float,
    significance_threshold: float | None,
    cluster_count: int,
) -> tuple[RegressionCoefficient, ...]:
    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0))
    critical = stats.t.ppf(1 - (1 - confidence_level) / 2, residual_df)
    coefficients: list[RegressionCoefficient] = []
    for index, variable_id in enumerate(predictor_variable_ids):
        estimate = safe_float(beta[index])
        standard_error = safe_float(standard_errors[index])
        test_statistic = None
        p_value = None
        low = None
        high = None
        below = None
        if estimate is not None and standard_error is not None and standard_error > 0:
            test_statistic = safe_float(estimate / standard_error)
            if test_statistic is not None:
                p_value = safe_float(2 * stats.t.sf(abs(test_statistic), residual_df))
            margin = safe_float(critical * standard_error)
            if margin is not None:
                low = safe_float(estimate - margin)
                high = safe_float(estimate + margin)
            if significance_threshold is not None and p_value is not None:
                below = p_value < significance_threshold
        coefficients.append(
            RegressionCoefficient(
                term=variable_id,
                variable_id=variable_id,
                estimate=estimate,
                standard_error=standard_error,
                test_statistic=test_statistic,
                p_value=p_value,
                confidence_interval_low=low,
                confidence_interval_high=high,
                below_significance_threshold=below,
                standard_error_type="cluster_robust_entity",
                cluster_count=cluster_count,
            )
        )
    return tuple(coefficients)


def _panel_sample_summary(
    sample: AnalysisSample,
    *,
    entities: tuple[str, ...],
    times: tuple[float, ...],
    cluster_count: int,
    lag_exclusions: int,
) -> PanelSampleSummary:
    counts = Counter(entities)
    unique_times = sorted(set(times))
    balanced = len(set(counts.values())) == 1 and all(
        count == len(unique_times) for count in counts.values()
    )
    return PanelSampleSummary(
        input_rows=sample.sample_size + len(sample.exclusions),
        included_rows=sample.sample_size,
        excluded_rows=len(sample.exclusions),
        entity_count=len(counts),
        time_period_count=len(unique_times),
        min_observations_per_entity=min(counts.values()) if counts else None,
        max_observations_per_entity=max(counts.values()) if counts else None,
        balanced=balanced,
        year_range=(unique_times[0], unique_times[-1]) if unique_times else None,
        lag_induced_exclusions=lag_exclusions,
        missing_data_exclusions=len(sample.exclusions),
        singleton_entity_exclusions=sum(1 for count in counts.values() if count == 1),
        cluster_count=cluster_count,
        effective_model_sample=sample.sample_size,
    )


def _panel_warnings(summary: PanelSampleSummary) -> list[AnalysisFinding]:
    warnings = [
        AnalysisFinding(
            severity=FindingSeverity.INFO,
            code=AnalysisFindingCode.SERIAL_CORRELATION_CAUTION,
            message=(
                "entity-clustered standard errors account for within-entity dependence in "
                "uncertainty estimates but do not eliminate every serial-correlation concern"
            ),
            method="panel_regression",
        ),
        AnalysisFinding(
            severity=FindingSeverity.INFO,
            code=AnalysisFindingCode.CROSS_SECTIONAL_DEPENDENCE_LIMITATION,
            message=(
                "year fixed effects can absorb common year shocks, but Phase 21 does not "
                "estimate cross-sectional dependence corrections"
            ),
            method="panel_regression",
        ),
    ]
    if not summary.balanced:
        warnings.append(
            AnalysisFinding(
                severity=FindingSeverity.INFO,
                code=AnalysisFindingCode.UNBALANCED_PANEL,
                message=(
                    "panel sample is unbalanced; Polaris does not fabricate missing entity-years"
                ),
                method="panel_regression",
            )
        )
    return warnings


def _variation(
    sample: AnalysisSample,
    variable_ids: tuple[str, ...],
    entity_variable_id: str,
) -> tuple[PanelVariableVariation, ...]:
    rows_by_entity = _rows_by_entity(sample.rows, entity_variable_id)
    results: list[PanelVariableVariation] = []
    for variable_id in variable_ids:
        values = np.asarray([row[variable_id] for row in sample.rows], dtype=float)
        entity_means = np.asarray(
            [np.mean([row[variable_id] for row in rows]) for rows in rows_by_entity.values()],
            dtype=float,
        )
        within_values = []
        for rows in rows_by_entity.values():
            group = np.asarray([row[variable_id] for row in rows], dtype=float)
            within_values.extend((group - np.mean(group)).tolist())
        overall_std = safe_float(np.std(values, ddof=1)) if values.size > 1 else None
        within_std = safe_float(np.std(within_values, ddof=1)) if len(within_values) > 1 else None
        between_std = safe_float(np.std(entity_means, ddof=1)) if entity_means.size > 1 else None
        low_within = (
            overall_std is not None
            and within_std is not None
            and overall_std > 0
            and within_std / overall_std < LOW_WITHIN_VARIATION_RATIO
        )
        results.append(
            PanelVariableVariation(
                variable_id=variable_id,
                overall_mean=safe_float(np.mean(values)),
                overall_standard_deviation=overall_std,
                within_entity_standard_deviation=within_std,
                between_entity_standard_deviation=between_std,
                low_within_variation=low_within,
            )
        )
    return tuple(results)


def _variation_warnings(variation: tuple[PanelVariableVariation, ...]) -> list[AnalysisFinding]:
    return [
        AnalysisFinding(
            severity=FindingSeverity.WARNING,
            code=AnalysisFindingCode.LOW_WITHIN_VARIATION,
            message=f'variable "{item.variable_id}" has little within-entity variation',
            variable_ids=(item.variable_id,),
            method="panel_regression",
        )
        for item in variation
        if item.low_within_variation
    ]


def _fit_metrics(
    *,
    y: np.ndarray,
    x: np.ndarray,
    beta: np.ndarray,
    entities: tuple[str, ...],
    transformed_y: np.ndarray,
    residuals: np.ndarray,
    residual_df: float,
    parameter_count: int,
) -> PanelFitMetrics:
    within_tss = float(np.sum((transformed_y - np.mean(transformed_y)) ** 2))
    within_r2 = (
        None if within_tss == 0 else safe_float(1 - float(np.sum(residuals**2)) / within_tss)
    )
    adjusted = None
    if within_r2 is not None and residual_df > 0 and y.size > 1:
        adjusted = safe_float(1 - (1 - within_r2) * (y.size - 1) / residual_df)
    fitted = x @ beta
    overall_tss = float(np.sum((y - np.mean(y)) ** 2))
    overall_r2 = (
        None if overall_tss == 0 else safe_float(1 - float(np.sum((y - fitted) ** 2)) / overall_tss)
    )
    entity_rows = _rows_by_entity_index(entities)
    y_means = []
    fitted_means = []
    for indexes in entity_rows.values():
        y_means.append(float(np.mean(y[indexes])))
        fitted_means.append(float(np.mean(fitted[indexes])))
    between_tss = float(np.sum((np.asarray(y_means) - np.mean(y_means)) ** 2))
    between_r2 = (
        None
        if between_tss == 0
        else safe_float(
            1 - float(np.sum((np.asarray(y_means) - np.asarray(fitted_means)) ** 2)) / between_tss
        )
    )
    return PanelFitMetrics(
        within_r_squared=within_r2,
        between_r_squared=between_r2,
        overall_r_squared=overall_r2,
        adjusted_within_r_squared=adjusted,
    )


def _rows_by_entity(
    rows: tuple[dict[str, int | float | str | bool], ...],
    entity_variable_id: str,
) -> dict[str, list[dict[str, int | float | str | bool]]]:
    grouped: dict[str, list[dict[str, int | float | str | bool]]] = {}
    for row in rows:
        grouped.setdefault(str(row[entity_variable_id]), []).append(row)
    return grouped


def _rows_by_entity_index(entities: tuple[str, ...]) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = {}
    for index, entity in enumerate(entities):
        grouped.setdefault(entity, []).append(index)
    return grouped


def _regression_summary(values: np.ndarray) -> RegressionSummary:
    count, mean, std, minimum, maximum = summarize(values.tolist())
    return RegressionSummary(
        count=count,
        mean=mean,
        standard_deviation=std,
        minimum=minimum,
        maximum=maximum,
    )
