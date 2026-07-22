"""Ordinary least squares regression with NumPy/SciPy inference."""

import numpy as np
from scipy import stats

from polaris.analysis.errors import RegressionExecutionError
from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisFindingCode,
    FindingSeverity,
    OLSRegressionResult,
    RegressionCoefficient,
    RegressionSummary,
)
from polaris.analysis.sample import AnalysisSample
from polaris.analysis.utils import safe_float, summarize


def fit_ols(
    sample: AnalysisSample,
    *,
    dependent_variable_id: str,
    predictor_variable_ids: tuple[str, ...],
    include_intercept: bool,
    confidence_level: float,
    significance_threshold: float | None,
) -> OLSRegressionResult:
    try:
        y = np.asarray([row[dependent_variable_id] for row in sample.rows], dtype=float)
        predictors = np.asarray(
            [[row[variable_id] for variable_id in predictor_variable_ids] for row in sample.rows],
            dtype=float,
        )
        x = np.column_stack([np.ones(len(y)), predictors]) if include_intercept else predictors
        rank = int(np.linalg.matrix_rank(x))
        beta = np.linalg.pinv(x) @ y
        fitted = x @ beta
        residuals = y - fitted
        nobs = int(y.size)
        parameter_count = int(x.shape[1])
        residual_df = float(nobs - rank)
        model_df = float(rank - 1) if include_intercept else float(rank)
        rss = safe_float(np.sum(residuals**2))
        mse = (
            safe_float((rss or 0.0) / residual_df) if residual_df > 0 and rss is not None else None
        )
        centered_tss = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = (
            None
            if centered_tss == 0
            else safe_float(1 - float(np.sum(residuals**2)) / centered_tss)
        )
        adjusted_r_squared = None
        if r_squared is not None and residual_df > 0 and nobs > 1:
            adjusted_r_squared = safe_float(1 - (1 - r_squared) * (nobs - 1) / residual_df)

        warnings: list[AnalysisFinding] = []
        if rank < parameter_count:
            warnings.append(
                AnalysisFinding(
                    severity=FindingSeverity.WARNING,
                    code=AnalysisFindingCode.SINGULAR_DESIGN_MATRIX,
                    message=(
                        "OLS design matrix is rank deficient; coefficients use a pseudo-inverse"
                    ),
                    variable_ids=predictor_variable_ids,
                    method="ordinary_least_squares",
                )
            )
        coefficients = _coefficients(
            x,
            beta,
            residual_df=residual_df,
            mse=mse,
            include_intercept=include_intercept,
            predictor_variable_ids=predictor_variable_ids,
            confidence_level=confidence_level,
            significance_threshold=significance_threshold,
        )
        return OLSRegressionResult(
            dependent_variable_id=dependent_variable_id,
            predictor_variable_ids=predictor_variable_ids,
            sample_size=nobs,
            coefficients=coefficients,
            include_intercept=include_intercept,
            r_squared=r_squared,
            adjusted_r_squared=adjusted_r_squared,
            residual_degrees_of_freedom=residual_df,
            model_degrees_of_freedom=model_df,
            residual_sum_of_squares=rss,
            mean_squared_error=mse,
            fitted_value_summary=_regression_summary(fitted),
            residual_summary=_regression_summary(residuals),
            warnings=tuple(warnings),
        )
    except Exception as exc:
        raise RegressionExecutionError("OLS regression execution failed") from exc


def _coefficients(
    x: np.ndarray,
    beta: np.ndarray,
    *,
    residual_df: float,
    mse: float | None,
    include_intercept: bool,
    predictor_variable_ids: tuple[str, ...],
    confidence_level: float,
    significance_threshold: float | None,
) -> tuple[RegressionCoefficient, ...]:
    if mse is None or residual_df <= 0:
        standard_errors = np.full(beta.shape, np.nan)
    else:
        covariance = mse * np.linalg.pinv(x.T @ x)
        standard_errors = np.sqrt(np.diag(covariance))
    alpha = 1 - confidence_level
    critical = stats.t.ppf(1 - alpha / 2, residual_df) if residual_df > 0 else np.nan
    terms: list[tuple[str, str | None]] = []
    if include_intercept:
        terms.append(("intercept", None))
    terms.extend((variable_id, variable_id) for variable_id in predictor_variable_ids)
    coefficients: list[RegressionCoefficient] = []
    for index, (term, variable_id) in enumerate(terms):
        estimate = safe_float(beta[index])
        standard_error = safe_float(standard_errors[index])
        test_statistic = None
        p_value = None
        low = None
        high = None
        below = None
        if (
            estimate is not None
            and standard_error is not None
            and standard_error > 0
            and residual_df > 0
        ):
            test_statistic = safe_float(estimate / standard_error)
            if test_statistic is not None:
                p_value = safe_float(2 * stats.t.sf(abs(test_statistic), residual_df))
            interval_margin = safe_float(critical * standard_error)
            if interval_margin is not None:
                low = safe_float(estimate - interval_margin)
                high = safe_float(estimate + interval_margin)
            if significance_threshold is not None and p_value is not None:
                below = p_value < significance_threshold
        coefficients.append(
            RegressionCoefficient(
                term=term,
                variable_id=variable_id,
                estimate=estimate,
                standard_error=standard_error,
                test_statistic=test_statistic,
                p_value=p_value,
                confidence_interval_low=low,
                confidence_interval_high=high,
                below_significance_threshold=below,
            )
        )
    return tuple(coefficients)


def _regression_summary(values: np.ndarray) -> RegressionSummary:
    count, mean, std, minimum, maximum = summarize(values.tolist())
    return RegressionSummary(
        count=count,
        mean=mean,
        standard_deviation=std,
        minimum=minimum,
        maximum=maximum,
    )
