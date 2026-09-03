"""Build plotting-ready Phase 25 visualization artifacts from existing results."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from polaris.analysis.causal.models import CausalAnalysisResult
from polaris.analysis.models import (
    AnalysisResult,
    CorrelationAnalysisResult,
    OLSRegressionResult,
    PanelRegressionResult,
    RegressionCoefficient,
)
from polaris.analysis.robustness.models import RobustnessAnalysisResult
from polaris.causal_studies.models import CausalStudyDefinition
from polaris.harmonization.models import HarmonizedDataset
from polaris.ingestion.models import DatasetIngestionResult
from polaris.visualization.errors import (
    IncompatibleVisualizationError,
    UnsupportedVisualizationError,
    VisualizationDataError,
    VisualizationSpecificationError,
)
from polaris.visualization.models import (
    Annotation,
    AxisMetadata,
    LegendEntry,
    ReferenceLine,
    ReferenceLineOrientation,
    VisualizationArtifact,
    VisualizationSpecification,
    VisualizationType,
    deterministic_visualization_id,
)


def build_visualization(
    *,
    specification: VisualizationSpecification,
    source_artifact: object,
    data_artifact: DatasetIngestionResult | HarmonizedDataset | None = None,
    comparison_artifacts: tuple[object, ...] = (),
) -> VisualizationArtifact:
    """Build a deterministic visualization artifact without estimating new models."""

    builder = _BUILDERS.get(specification.visualization_type)
    if builder is None:
        raise UnsupportedVisualizationError(
            f"unsupported visualization type: {specification.visualization_type.value}"
        )
    artifact = builder(specification, source_artifact, data_artifact, comparison_artifacts)
    _validate_visual_integrity(artifact)
    return artifact


def _country_trend(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del comparison_artifacts
    dataset = _require_dataset(data_artifact or source)
    variable = spec.y_variable or _single_selected_variable(spec)
    entity_var = spec.entity_variable or "country"
    time_var = spec.time_variable or "year"
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    catalog = _variable_catalog(dataset)
    selected = set(spec.selected_entities)
    for row in _dataset_rows(dataset):
        entity = _row_get(row, entity_var) or _row_get(row, "canonical_country_code")
        year = _row_get(row, time_var) or _row_get(row, "year")
        value = _row_get(row, variable)
        if entity not in selected or not _in_time_range(year, spec.time_range):
            continue
        rows.append(
            {
                "entity": entity,
                "year": year,
                "variable": variable,
                "value": value,
                "missing": value is None,
            }
        )
    rows = sorted(rows, key=lambda item: (str(item["entity"]), item["year"]))
    if not rows:
        raise VisualizationDataError("country trend has no rows for requested entities/time range")
    observed_years_by_entity: dict[str, set[int | float]] = defaultdict(set)
    for row in rows:
        if row["value"] is not None:
            observed_years_by_entity[str(row["entity"])].add(row["year"])
    all_years = sorted({row["year"] for row in rows})
    for entity in spec.selected_entities:
        missing_years = [year for year in all_years if year not in observed_years_by_entity[entity]]
        if missing_years:
            warnings.append(
                f"{entity} has missing observations for years: "
                + ", ".join(str(year) for year in missing_years)
            )
    title = spec.title or f"{_label(spec, variable, catalog)} Over Time"
    return _artifact(
        spec,
        source_ids=(_source_id(source, dataset),),
        source_provenance=_source_provenance(source, dataset),
        plotting_data=tuple(rows),
        axis_metadata={
            "x": AxisMetadata(variable_id=time_var, label=_label(spec, time_var, catalog)),
            "y": AxisMetadata(
                variable_id=variable,
                label=_label(spec, variable, catalog),
                unit=_unit(spec, variable, catalog),
            ),
        },
        legend=tuple(LegendEntry(key=entity, label=entity) for entity in spec.selected_entities),
        annotations=(
            Annotation(text="Missing observations are represented as absent plotted points."),
        ),
        warnings=tuple(warnings),
        title=title,
    )


def _scatterplot(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del comparison_artifacts
    x_var = _require_field(spec.x_variable, "x_variable")
    y_var = _require_field(spec.y_variable, "y_variable")
    rows = []
    catalog: dict[str, dict[str, str | None]] = {}
    if isinstance(source, AnalysisResult):
        for sample_row in _analysis_sample_rows(source, data_artifact):
            rows.append(
                {
                    "x": sample_row.get(x_var),
                    "y": sample_row.get(y_var),
                    "entity": sample_row.get(spec.entity_variable or "country"),
                    "time": sample_row.get(spec.time_variable or "year"),
                    "source_sample": source.result_id,
                }
            )
    else:
        dataset = _require_dataset(data_artifact or source)
        catalog = _variable_catalog(dataset)
        for row in _dataset_rows(dataset):
            x = _row_get(row, x_var)
            y = _row_get(row, y_var)
            if x is None or y is None:
                continue
            rows.append(
                {
                    "x": x,
                    "y": y,
                    "entity": _row_get(row, spec.entity_variable or "country"),
                    "time": _row_get(row, spec.time_variable or "year"),
                }
            )
    rows = tuple(sorted(rows, key=lambda item: (str(item.get("entity")), str(item.get("time")))))
    if not rows:
        raise VisualizationDataError("scatterplot has no complete plotted observations")
    title = spec.title or f"{_label(spec, x_var, catalog)} and {_label(spec, y_var, catalog)}"
    return _artifact(
        spec,
        source_ids=(_source_id(source, data_artifact),),
        source_provenance=_source_provenance(source, data_artifact),
        plotting_data=rows,
        axis_metadata={
            "x": AxisMetadata(
                variable_id=x_var,
                label=_label(spec, x_var, catalog),
                unit=_unit(spec, x_var, catalog),
            ),
            "y": AxisMetadata(
                variable_id=y_var,
                label=_label(spec, y_var, catalog),
                unit=_unit(spec, y_var, catalog),
            ),
        },
        annotations=(Annotation(text="Scatterplot uses the supplied analytical sample."),)
        if isinstance(source, AnalysisResult)
        else (),
        title=title,
    )


def _regression_relationship(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    artifact = _scatterplot(spec, source, data_artifact, comparison_artifacts)
    if not isinstance(source, AnalysisResult) or not isinstance(
        source.method_result, OLSRegressionResult
    ):
        return artifact.model_copy(
            update={
                "warnings": (
                    *artifact.warnings,
                    "Fitted relationship omitted because source is not an OLS AnalysisResult.",
                )
            }
        )
    result = source.method_result
    if len(result.predictor_variable_ids) != 1 or result.coefficients[0].estimate is None:
        return artifact.model_copy(
            update={
                "warnings": (
                    *artifact.warnings,
                    "Fitted line omitted because existing model has multiple predictors "
                    "or no intercept.",
                )
            }
        )
    intercept = next(
        (coef.estimate for coef in result.coefficients if coef.term == "intercept"), None
    )
    slope = next(
        (
            coef.estimate
            for coef in result.coefficients
            if coef.variable_id == result.predictor_variable_ids[0]
        ),
        None,
    )
    if intercept is None or slope is None:
        return artifact.model_copy(
            update={
                "warnings": (
                    *artifact.warnings,
                    "Fitted line omitted; coefficients cannot be reconstructed.",
                )
            }
        )
    xs = sorted(row["x"] for row in artifact.plotting_data if isinstance(row["x"], int | float))
    fit_rows = (
        {"x": xs[0], "y": intercept + slope * xs[0], "series": "existing_ols_fitted_line"},
        {"x": xs[-1], "y": intercept + slope * xs[-1], "series": "existing_ols_fitted_line"},
    )
    return artifact.model_copy(
        update={
            "plotting_data": (*artifact.plotting_data, *fit_rows),
            "legend": (
                LegendEntry(key="observations", label="Observations"),
                LegendEntry(key="existing_ols_fitted_line", label="Existing OLS fitted line"),
            ),
            "annotations": (
                *artifact.annotations,
                Annotation(text="Fitted line is reconstructed from existing Phase 4 coefficients."),
            ),
        }
    )


def _coefficient_plot(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    model_result = _model_result(source)
    coefficients = _selected_coefficients(model_result.coefficients, spec.selected_terms)
    rows = tuple(
        {
            "term": coef.term,
            "variable": coef.variable_id,
            "estimate": coef.estimate,
            "confidence_interval_low": coef.confidence_interval_low,
            "confidence_interval_high": coef.confidence_interval_high,
            "p_value": coef.p_value,
            "model_id": _source_id(source, None),
            "sample_size": model_result.sample_size,
        }
        for coef in coefficients
    )
    if not rows:
        raise VisualizationDataError("coefficient plot has no coefficients")
    return _artifact(
        spec,
        source_ids=(_source_id(source, None),),
        source_provenance=_source_provenance(source, None),
        plotting_data=rows,
        axis_metadata={
            "x": AxisMetadata(label="Estimate"),
            "y": AxisMetadata(label="Coefficient"),
        },
        annotations=(Annotation(text="Non-significant coefficients are retained."),),
        title=spec.title or "Coefficient Estimates",
    )


def _model_comparison(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact
    artifacts = (source, *comparison_artifacts)
    term = _single_selected_term(spec)
    rows = []
    source_ids = []
    for artifact in artifacts:
        result = _model_result(artifact)
        coef = next(
            (item for item in result.coefficients if item.term == term or item.variable_id == term),
            None,
        )
        if coef is None:
            raise IncompatibleVisualizationError(
                f"model {_source_id(artifact, None)} lacks term {term}"
            )
        if result.dependent_variable_id != _model_result(source).dependent_variable_id:
            raise IncompatibleVisualizationError(
                "model comparison requires common outcome variable"
            )
        rows.append(
            {
                "model_id": _source_id(artifact, None),
                "model_type": getattr(
                    result, "procedure", getattr(artifact, "analysis_method", "ols")
                ).value
                if hasattr(
                    getattr(result, "procedure", getattr(artifact, "analysis_method", "ols")),
                    "value",
                )
                else str(getattr(result, "procedure", getattr(artifact, "analysis_method", "ols"))),
                "term": term,
                "estimate": coef.estimate,
                "confidence_interval_low": coef.confidence_interval_low,
                "confidence_interval_high": coef.confidence_interval_high,
                "sample_size": result.sample_size,
            }
        )
        source_ids.append(_source_id(artifact, None))
    return _artifact(
        spec,
        source_ids=tuple(source_ids),
        source_provenance={"model_ids": tuple(source_ids)},
        plotting_data=tuple(rows),
        axis_metadata={"x": AxisMetadata(label="Estimate"), "y": AxisMetadata(label="Model")},
        annotations=(Annotation(text="Only the explicitly selected common estimand is compared."),),
        title=spec.title or "Compatible Model Estimate Comparison",
    )


def _event_study(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    if not isinstance(source, CausalAnalysisResult):
        raise UnsupportedVisualizationError(
            "event-study visualization requires CausalAnalysisResult"
        )
    rows = tuple(
        {
            "event_time": item.event_time,
            "estimate": item.coefficient,
            "confidence_interval_low": item.confidence_interval_low,
            "confidence_interval_high": item.confidence_interval_high,
            "p_value": item.p_value,
            "observation_count": item.observation_count,
            "treated_entity_count": item.treated_entity_count,
            "reference_period": item.reference_period,
            "pre_post_status": item.pre_post_status,
            "missing_period": item.coefficient is None and not item.reference_period,
        }
        for item in sorted(source.event_study_results, key=lambda item: item.event_time)
    )
    if not rows:
        raise VisualizationDataError("event-study source contains no event-time coefficients")
    reference = next((row["event_time"] for row in rows if row["reference_period"]), None)
    annotations = [
        Annotation(text="Event-time ordering and omitted reference period are preserved."),
        Annotation(text="Flat pre-treatment estimates do not prove parallel trends."),
    ]
    if reference is not None:
        annotations.append(Annotation(text=f"Omitted reference period: {reference}"))
    return _artifact(
        spec,
        source_ids=(source.causal_analysis_id,),
        source_provenance=_source_provenance(source, None),
        plotting_data=rows,
        axis_metadata={
            "x": AxisMetadata(label="Event Time"),
            "y": AxisMetadata(
                variable_id=source.causal_specification.outcome_variable.variable_id,
                label="Estimate",
            ),
        },
        annotations=tuple(annotations),
        reference_lines=(
            ReferenceLine(
                orientation=ReferenceLineOrientation.X, value=0, label="Treatment period"
            ),
            ReferenceLine(orientation=ReferenceLineOrientation.Y, value=0, label="Zero effect"),
        ),
        title=spec.title or "Event-Study Estimates Relative to Treatment",
    )


def _causal_estimate(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    if not isinstance(source, CausalAnalysisResult):
        raise UnsupportedVisualizationError(
            "causal estimate visualization requires CausalAnalysisResult"
        )
    effect = source.treatment_effect
    rows = (
        {
            "method": source.method.value,
            "estimator": source.estimator.value,
            "estimand": effect.estimand.value,
            "term": effect.term,
            "estimate": effect.estimate,
            "confidence_interval_low": effect.confidence_interval_low,
            "confidence_interval_high": effect.confidence_interval_high,
            "sample_size": source.sample_summary.included_rows,
            "treated_entities": source.sample_summary.treated_entity_count,
            "control_entities": source.sample_summary.control_entity_count,
        },
    )
    return _artifact(
        spec,
        source_ids=(source.causal_analysis_id,),
        source_provenance=_source_provenance(source, None),
        plotting_data=rows,
        axis_metadata={
            "x": AxisMetadata(label="Estimate"),
            "y": AxisMetadata(label="Causal Estimand"),
        },
        annotations=(
            Annotation(text="Identifying assumptions remain limitations of the causal design."),
        ),
        title=spec.title or "Causal Treatment Estimate",
    )


def _robustness_estimates(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    robustness = _require_robustness(source)
    rows = list(robustness.plotting_artifacts.get("robustness_estimates.csv", ()))
    if not rows:
        baseline_effect = robustness.baseline_result.treatment_effect
        rows = [
            {
                "variant_id": "baseline",
                "variant_type": "baseline",
                "estimate": baseline_effect.estimate,
                "confidence_interval_low": baseline_effect.confidence_interval_low,
                "confidence_interval_high": baseline_effect.confidence_interval_high,
                "status": "baseline",
            }
        ]
        rows.extend(
            {
                "variant_id": item.variant_id,
                "variant_type": item.variant_type.value,
                "estimate": item.analysis_result.treatment_effect.estimate,
                "confidence_interval_low": (
                    item.analysis_result.treatment_effect.confidence_interval_low
                ),
                "confidence_interval_high": (
                    item.analysis_result.treatment_effect.confidence_interval_high
                ),
                "status": "successful",
            }
            for item in robustness.variant_results
        )
    rows.extend(
        {
            "variant_id": item.variant_id,
            "variant_type": item.variant_type.value,
            "estimate": None,
            "confidence_interval_low": None,
            "confidence_interval_high": None,
            "status": "failed",
            "failure_reason": item.reason,
        }
        for item in robustness.failed_variants
    )
    return _robustness_artifact(
        spec,
        robustness,
        tuple(rows),
        "Estimated Treatment Effects Across Robustness Specifications",
    )


def _leave_one_out(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    robustness = _require_robustness(source)
    rows = [
        {
            "omitted_entity": item.omitted_entity,
            "omitted_role": item.omitted_role,
            "estimate": item.treatment_estimate,
            "confidence_interval_low": item.confidence_interval_low,
            "confidence_interval_high": item.confidence_interval_high,
            "baseline_estimate": robustness.baseline_result.treatment_effect.estimate,
            "sample_size": item.sample_size,
            "low_cluster_warning": item.low_cluster_warning,
        }
        for item in sorted(
            robustness.leave_one_out_results,
            key=lambda item: (item.omitted_role, item.omitted_entity),
        )
    ]
    if not rows:
        raise VisualizationDataError("robustness source contains no leave-one-out results")
    return _robustness_artifact(
        spec, robustness, tuple(rows), "Leave-One-Out Treatment Estimate Diagnostics"
    )


def _placebo(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    robustness = _require_robustness(source)
    rows = [
        {
            "variant_id": item.variant_id,
            "placebo_year": item.placebo_year,
            "placebo_treated_entities": ",".join(item.placebo_treated_entities),
            "estimate": item.estimate,
            "confidence_interval_low": item.confidence_interval_low,
            "confidence_interval_high": item.confidence_interval_high,
            "baseline_estimate": robustness.baseline_result.treatment_effect.estimate,
            "series": "placebo",
        }
        for item in sorted(robustness.placebo_results, key=lambda item: item.variant_id)
    ]
    if not rows:
        raise VisualizationDataError("robustness source contains no placebo results")
    baseline_effect = robustness.baseline_result.treatment_effect
    rows.append(
        {
            "variant_id": "actual_baseline",
            "placebo_year": None,
            "placebo_treated_entities": "",
            "estimate": baseline_effect.estimate,
            "confidence_interval_low": baseline_effect.confidence_interval_low,
            "confidence_interval_high": baseline_effect.confidence_interval_high,
            "baseline_estimate": baseline_effect.estimate,
            "series": "actual",
        }
    )
    return _robustness_artifact(spec, robustness, tuple(rows), "Placebo Estimate Diagnostics")


def _correlation_matrix(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    if not isinstance(source, AnalysisResult) or not isinstance(
        source.method_result, CorrelationAnalysisResult
    ):
        raise UnsupportedVisualizationError(
            "correlation matrix requires a correlation AnalysisResult"
        )
    selected = (
        set(spec.selected_variables)
        if spec.selected_variables
        else {
            var
            for pair in source.method_result.pairs
            for var in (pair.variable_id_1, pair.variable_id_2)
        }
    )
    rows = tuple(
        sorted(
            (
                {
                    "variable_1": pair.variable_id_1,
                    "variable_2": pair.variable_id_2,
                    "correlation": pair.correlation_coefficient,
                    "p_value": pair.p_value,
                    "observation_count": pair.observation_count,
                    "method": pair.method,
                }
                for pair in source.method_result.pairs
                if pair.variable_id_1 in selected and pair.variable_id_2 in selected
            ),
            key=lambda item: (item["variable_1"], item["variable_2"]),
        )
    )
    if not rows:
        raise VisualizationDataError("correlation source contains no selected pairs")
    return _artifact(
        spec,
        source_ids=(source.result_id,),
        source_provenance=_source_provenance(source, None),
        plotting_data=rows,
        axis_metadata={"x": AxisMetadata(label="Variable"), "y": AxisMetadata(label="Variable")},
        annotations=(Annotation(text="Correlation values are existing Phase 4 results."),),
        title=spec.title or "Correlation Matrix",
    )


def _missingness(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del comparison_artifacts
    dataset = _require_dataset(data_artifact or source)
    variables = spec.selected_variables or tuple(_variable_catalog(dataset).keys())
    rows: list[dict[str, Any]] = []
    records = _dataset_rows(dataset)
    if spec.visualization_type is VisualizationType.MISSINGNESS_BY_VARIABLE:
        for variable in variables:
            missing = sum(1 for row in records if _row_get(row, variable) is None)
            rows.append(
                {
                    "variable": variable,
                    "missing_count": missing,
                    "total_count": len(records),
                    "missing_rate": missing / len(records) if records else 0,
                }
            )
    elif spec.visualization_type is VisualizationType.MISSINGNESS_BY_YEAR:
        by_year: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for row in records:
            by_year[_row_get(row, spec.time_variable or "year")].append(row)
        for year, year_rows in sorted(by_year.items()):
            missing = sum(
                1 for row in year_rows for variable in variables if _row_get(row, variable) is None
            )
            total = len(year_rows) * len(variables)
            rows.append(
                {
                    "year": year,
                    "missing_count": missing,
                    "total_count": total,
                    "missing_rate": missing / total if total else 0,
                }
            )
    else:
        by_entity: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for row in records:
            by_entity[_row_get(row, spec.entity_variable or "country")].append(row)
        for entity, entity_rows in sorted(by_entity.items()):
            missing = sum(
                1
                for row in entity_rows
                for variable in variables
                if _row_get(row, variable) is None
            )
            total = len(entity_rows) * len(variables)
            rows.append(
                {
                    "entity": entity,
                    "missing_count": missing,
                    "total_count": total,
                    "missing_rate": missing / total if total else 0,
                }
            )
    return _artifact(
        spec,
        source_ids=(_source_id(source, dataset),),
        source_provenance=_source_provenance(source, dataset),
        plotting_data=tuple(rows),
        axis_metadata={
            "x": AxisMetadata(label="Category"),
            "y": AxisMetadata(label="Missing Rate"),
        },
        annotations=(Annotation(text="No imputation is performed."),),
        title=spec.title or "Missingness Diagnostics",
    )


def _coverage(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del comparison_artifacts
    dataset = _require_dataset(data_artifact or source)
    variables = spec.selected_variables or tuple(_variable_catalog(dataset).keys())
    rows = []
    for row in _dataset_rows(dataset):
        entity = _row_get(row, spec.entity_variable or "country")
        year = _row_get(row, spec.time_variable or "year")
        if spec.selected_entities and entity not in set(spec.selected_entities):
            continue
        if not _in_time_range(year, spec.time_range):
            continue
        observed = sum(1 for variable in variables if _row_get(row, variable) is not None)
        rows.append(
            {
                "entity": entity,
                "year": year,
                "observed_variable_count": observed,
                "required_variable_count": len(variables),
                "covered": observed == len(variables),
            }
        )
    rows = tuple(sorted(rows, key=lambda item: (str(item["entity"]), item["year"])))
    if not rows:
        raise VisualizationDataError("coverage diagnostic has no country-year rows")
    return _artifact(
        spec,
        source_ids=(_source_id(source, dataset),),
        source_provenance=_source_provenance(source, dataset),
        plotting_data=rows,
        axis_metadata={"x": AxisMetadata(label="Year"), "y": AxisMetadata(label="Entity")},
        annotations=(Annotation(text="Coverage distinguishes missing values from zero values."),),
        title=spec.title or "Country-Year Coverage",
    )


def _distribution(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del comparison_artifacts
    dataset = _require_dataset(data_artifact or source)
    variable = spec.x_variable or spec.y_variable or _single_selected_variable(spec)
    rows = tuple(
        sorted(
            (
                {
                    "variable": variable,
                    "value": _row_get(row, variable),
                    "entity": _row_get(row, spec.entity_variable or "country"),
                    "time": _row_get(row, spec.time_variable or "year"),
                }
                for row in _dataset_rows(dataset)
                if _row_get(row, variable) is not None
            ),
            key=lambda item: (str(item["entity"]), str(item["time"])),
        )
    )
    if not rows:
        raise VisualizationDataError("distribution diagnostic has no observed values")
    return _artifact(
        spec,
        source_ids=(_source_id(source, dataset),),
        source_provenance=_source_provenance(source, dataset),
        plotting_data=rows,
        axis_metadata={
            "x": AxisMetadata(
                variable_id=variable, label=_label(spec, variable, _variable_catalog(dataset))
            )
        },
        annotations=(Annotation(text="No automatic outlier removal is performed."),),
        title=spec.title or f"Distribution of {_label(spec, variable, _variable_catalog(dataset))}",
    )


def _panel_diagnostic(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    result = _model_result(source)
    if not isinstance(result, PanelRegressionResult):
        raise UnsupportedVisualizationError("panel diagnostics require PanelRegressionResult")
    kind = spec.panel_diagnostic
    if kind is None:
        raise VisualizationSpecificationError("panel_diagnostic is required")
    if kind.value == "within_between_variation":
        rows = tuple(item.model_dump(mode="json") for item in result.variation)
        title = "Within and Between Panel Variation"
    elif kind.value == "time_coverage":
        rows = (
            {
                "year_start": result.panel_sample.year_range[0]
                if result.panel_sample.year_range
                else None,
                "year_end": result.panel_sample.year_range[1]
                if result.panel_sample.year_range
                else None,
                "time_period_count": result.panel_sample.time_period_count,
                "balanced": result.panel_sample.balanced,
            },
        )
        title = "Panel Time Coverage"
    else:
        rows = (
            {
                "entity_count": result.panel_sample.entity_count,
                "included_rows": result.panel_sample.included_rows,
                "min_observations_per_entity": result.panel_sample.min_observations_per_entity,
                "max_observations_per_entity": result.panel_sample.max_observations_per_entity,
                "balanced": result.panel_sample.balanced,
            },
        )
        title = "Panel Observation Counts"
    return _artifact(
        spec,
        source_ids=(_source_id(source, None),),
        source_provenance=_source_provenance(source, None),
        plotting_data=rows,
        axis_metadata={
            "x": AxisMetadata(label="Panel Diagnostic"),
            "y": AxisMetadata(label="Value"),
        },
        title=spec.title or title,
    )


def _causal_study_diagnostic(
    spec: VisualizationSpecification,
    source: object,
    data_artifact: object | None,
    comparison_artifacts: tuple[object, ...],
) -> VisualizationArtifact:
    del data_artifact, comparison_artifacts
    if not isinstance(source, CausalStudyDefinition):
        raise UnsupportedVisualizationError(
            "causal study diagnostics require CausalStudyDefinition"
        )
    rows = []
    intervention = source.intervention
    assignments = sorted(source.treatment_assignments, key=lambda item: item.entity_id)
    for assignment in assignments:
        rows.append(
            {
                "study_id": source.study_id,
                "intervention_id": intervention.intervention_id,
                "entity": assignment.entity_id,
                "role": assignment.treatment_status.value,
                "treatment_start_period": assignment.treatment_start,
                "treatment_end_period": assignment.treatment_end,
                "event_window_min": (
                    source.event_study_window.min_event_time
                    if source.event_study_window is not None
                    else None
                ),
                "event_window_max": (
                    source.event_study_window.max_event_time
                    if source.event_study_window is not None
                    else None
                ),
                "pre_period_requirements": source.pre_period_requirements,
                "post_period_requirements": source.post_period_requirements,
            }
        )
    if not rows:
        raise VisualizationDataError("causal study contains no treated/control entities")
    return _artifact(
        spec,
        source_ids=(source.study_id,),
        source_provenance={"study_id": source.study_id, "schema_version": source.schema_version},
        plotting_data=tuple(
            sorted(rows, key=lambda item: (item["intervention_id"], item["role"], item["entity"]))
        ),
        axis_metadata={
            "x": AxisMetadata(label="Treatment Timing"),
            "y": AxisMetadata(label="Entity"),
        },
        annotations=(
            Annotation(text="Design metadata is shown before causal estimates are interpreted."),
        ),
        title=spec.title or "Causal Study Design Diagnostic",
    )


_BUILDERS = {
    VisualizationType.COUNTRY_TIME_SERIES: _country_trend,
    VisualizationType.MULTI_COUNTRY_TREND: _country_trend,
    VisualizationType.SCATTERPLOT: _scatterplot,
    VisualizationType.REGRESSION_RELATIONSHIP: _regression_relationship,
    VisualizationType.COEFFICIENT_PLOT: _coefficient_plot,
    VisualizationType.MODEL_COMPARISON: _model_comparison,
    VisualizationType.EVENT_STUDY: _event_study,
    VisualizationType.CAUSAL_ESTIMATE: _causal_estimate,
    VisualizationType.ROBUSTNESS_ESTIMATES: _robustness_estimates,
    VisualizationType.LEAVE_ONE_OUT: _leave_one_out,
    VisualizationType.PLACEBO: _placebo,
    VisualizationType.CORRELATION_MATRIX: _correlation_matrix,
    VisualizationType.MISSINGNESS_BY_VARIABLE: _missingness,
    VisualizationType.MISSINGNESS_BY_YEAR: _missingness,
    VisualizationType.MISSINGNESS_BY_ENTITY: _missingness,
    VisualizationType.COUNTRY_YEAR_COVERAGE: _coverage,
    VisualizationType.DISTRIBUTION_HISTOGRAM: _distribution,
    VisualizationType.DISTRIBUTION_BOX: _distribution,
    VisualizationType.PANEL_DIAGNOSTIC: _panel_diagnostic,
    VisualizationType.CAUSAL_STUDY_DIAGNOSTIC: _causal_study_diagnostic,
}


def _artifact(
    spec: VisualizationSpecification,
    *,
    source_ids: tuple[str, ...],
    source_provenance: dict[str, Any],
    plotting_data: tuple[dict[str, Any], ...],
    axis_metadata: dict[str, AxisMetadata],
    title: str,
    legend: tuple[LegendEntry, ...] = (),
    annotations: tuple[Annotation, ...] = (),
    warnings: tuple[str, ...] = (),
    reference_lines: tuple[ReferenceLine, ...] = (),
) -> VisualizationArtifact:
    final_spec = spec if spec.title else spec.model_copy(update={"title": title})
    references = (*spec.reference_lines, *reference_lines)
    annotations = (
        *annotations,
        *(
            Annotation(text=f"Reference line: {line.label or line.value}")
            for line in references
            if line.label is not None
        ),
    )
    visualization_id = deterministic_visualization_id(
        source_artifact_ids=source_ids,
        source_provenance=source_provenance,
        specification=final_spec,
    )
    return VisualizationArtifact(
        visualization_id=visualization_id,
        visualization_type=spec.visualization_type,
        source_artifact_ids=source_ids,
        specification=final_spec,
        plotting_data=plotting_data,
        axis_metadata=axis_metadata,
        legend=legend,
        annotations=annotations,
        warnings=warnings,
        limitations=(
            "Visualization is downstream of validated artifacts and does not create new "
            "empirical claims.",
        ),
        provenance=source_provenance,
    )


def _robustness_artifact(
    spec: VisualizationSpecification,
    robustness: RobustnessAnalysisResult,
    rows: tuple[dict[str, Any], ...],
    title: str,
) -> VisualizationArtifact:
    return _artifact(
        spec,
        source_ids=(robustness.robustness_analysis_id, robustness.baseline.baseline_analysis_id),
        source_provenance=_source_provenance(robustness, None),
        plotting_data=rows,
        axis_metadata={
            "x": AxisMetadata(label="Estimate"),
            "y": AxisMetadata(label="Specification"),
        },
        annotations=(
            Annotation(text="Failed variants are retained as failed rows."),
            Annotation(text="Robustness diagnostics do not prove causality."),
        ),
        title=spec.title or title,
    )


def _require_dataset(source: object) -> DatasetIngestionResult | HarmonizedDataset:
    if isinstance(source, DatasetIngestionResult | HarmonizedDataset):
        return source
    raise UnsupportedVisualizationError("visualization requires an ingestion or harmonized dataset")


def _require_robustness(source: object) -> RobustnessAnalysisResult:
    if not isinstance(source, RobustnessAnalysisResult):
        raise UnsupportedVisualizationError(
            "robustness visualization requires RobustnessAnalysisResult"
        )
    return source


def _dataset_rows(
    dataset: DatasetIngestionResult | HarmonizedDataset,
) -> tuple[dict[str, Any], ...]:
    if isinstance(dataset, DatasetIngestionResult):
        return tuple(record.values for record in dataset.normalized_records)
    return tuple(
        {
            "country": record.canonical_country_code,
            "country_name": record.canonical_country_name,
            "year": record.year,
            **record.values,
        }
        for record in dataset.records
    )


def _row_get(row: dict[str, Any], variable: str) -> Any:
    if variable in row:
        return row[variable]
    aliases = {
        "country": ("country_code", "iso3", "canonical_country_code", "entity"),
        "year": ("time", "period"),
    }
    for alias in aliases.get(variable, ()):
        if alias in row:
            return row[alias]
    return None


def _variable_catalog(
    dataset: DatasetIngestionResult | HarmonizedDataset,
) -> dict[str, dict[str, str | None]]:
    if isinstance(dataset, DatasetIngestionResult):
        return {
            variable.variable_id: {"label": variable.variable_id, "unit": None}
            for variable in dataset.quality_profile.variables
        }
    return {
        item.canonical_variable_id: {"label": item.canonical_label, "unit": item.unit}
        for item in dataset.canonical_variable_catalog
    }


def _analysis_sample_rows(
    source: AnalysisResult, data_artifact: object | None
) -> tuple[dict[str, Any], ...]:
    if data_artifact is None:
        raise VisualizationDataError("analysis-tied plots require data_artifact to preserve sample")
    dataset = _require_dataset(data_artifact)
    by_row_number = {
        getattr(record, "row_number", index): row
        for index, (record, row) in enumerate(
            zip(getattr(dataset, "normalized_records", ()), _dataset_rows(dataset), strict=False),
            start=1,
        )
    }
    if isinstance(dataset, HarmonizedDataset):
        rows = _dataset_rows(dataset)
        return tuple(
            rows[number - 1]
            for number in source.analysis_sample.included_row_numbers
            if 0 < number <= len(rows)
        )
    return tuple(
        by_row_number[number]
        for number in source.analysis_sample.included_row_numbers
        if number in by_row_number
    )


def _model_result(source: object) -> OLSRegressionResult | PanelRegressionResult:
    if isinstance(source, AnalysisResult) and isinstance(
        source.method_result, OLSRegressionResult | PanelRegressionResult
    ):
        return source.method_result
    if isinstance(source, CausalAnalysisResult) and source.regression_result is not None:
        return source.regression_result
    raise UnsupportedVisualizationError("source artifact does not contain model coefficients")


def _selected_coefficients(
    coefficients: tuple[RegressionCoefficient, ...],
    selected_terms: tuple[str, ...],
) -> tuple[RegressionCoefficient, ...]:
    selected = set(selected_terms)
    return tuple(
        coef
        for coef in coefficients
        if coef.term != "intercept"
        and (not selected or coef.term in selected or coef.variable_id in selected)
    )


def _single_selected_variable(spec: VisualizationSpecification) -> str:
    if len(spec.selected_variables) != 1:
        raise VisualizationSpecificationError("exactly one selected variable is required")
    return spec.selected_variables[0]


def _single_selected_term(spec: VisualizationSpecification) -> str:
    if len(spec.selected_terms) != 1:
        raise VisualizationSpecificationError("model comparison requires exactly one selected term")
    return spec.selected_terms[0]


def _require_field(value: str | None, name: str) -> str:
    if value is None:
        raise VisualizationSpecificationError(f"{name} is required")
    return value


def _label(
    spec: VisualizationSpecification,
    variable: str,
    catalog: dict[str, dict[str, str | None]],
) -> str:
    return spec.labels.get(variable) or catalog.get(variable, {}).get("label") or variable


def _unit(
    spec: VisualizationSpecification,
    variable: str,
    catalog: dict[str, dict[str, str | None]],
) -> str | None:
    return spec.units.get(variable) or catalog.get(variable, {}).get("unit")


def _in_time_range(value: object, time_range: tuple[int | float, int | float] | None) -> bool:
    if time_range is None:
        return True
    if not isinstance(value, int | float):
        return False
    return time_range[0] <= value <= time_range[1]


def _source_id(source: object, data_artifact: object | None) -> str:
    for attr in (
        "result_id",
        "causal_analysis_id",
        "robustness_analysis_id",
        "harmonized_dataset_id",
        "study_id",
    ):
        value = getattr(source, attr, None)
        if value is not None:
            return str(value)
    if isinstance(source, DatasetIngestionResult):
        return source.dataset_manifest.dataset_id
    if isinstance(data_artifact, DatasetIngestionResult):
        return data_artifact.dataset_manifest.dataset_id
    if isinstance(data_artifact, HarmonizedDataset):
        return data_artifact.harmonized_dataset_id
    return "unknown_source_artifact"


def _source_provenance(source: object, data_artifact: object | None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for attr in ("dataset_id", "source_checksum_sha256", "schema_version", "ruleset_version"):
        value = getattr(source, attr, None)
        if value is not None:
            payload[attr] = value
    if isinstance(source, DatasetIngestionResult):
        payload.update(
            {"dataset_id": source.dataset_manifest.dataset_id, "checksum": source.checksum_sha256}
        )
    if isinstance(data_artifact, DatasetIngestionResult):
        payload.update(
            {
                "data_dataset_id": data_artifact.dataset_manifest.dataset_id,
                "data_checksum": data_artifact.checksum_sha256,
            }
        )
    if isinstance(data_artifact, HarmonizedDataset):
        payload.update(
            {
                "harmonized_dataset_id": data_artifact.harmonized_dataset_id,
                "source_checksums": data_artifact.source_checksums,
            }
        )
    return payload


def _validate_visual_integrity(artifact: VisualizationArtifact) -> None:
    title = artifact.specification.title or ""
    banned = ("improves", "causes", "proves", "drives")
    if any(word in title.lower() for word in banned):
        raise VisualizationSpecificationError(
            "visualization titles must not use unsupported causal wording"
        )
    for axis in artifact.axis_metadata.values():
        if axis.truncated and not artifact.specification.axis_truncation_allowed:
            raise VisualizationSpecificationError(
                "axis truncation must be explicit in the specification"
            )
