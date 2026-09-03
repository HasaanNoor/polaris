"""Deterministic matplotlib rendering for Phase 25 visualization artifacts."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from polaris.visualization.errors import VisualizationRenderingError
from polaris.visualization.models import OutputFormat, VisualizationArtifact, VisualizationType

os.environ.setdefault("MPLCONFIGDIR", str(Path(gettempdir()) / "polaris-matplotlib"))


def render_visualization(
    artifact: VisualizationArtifact,
    *,
    output_path: Path,
    output_format: OutputFormat,
) -> Path:
    """Render one visualization artifact to PNG or SVG."""

    if output_format not in {OutputFormat.PNG, OutputFormat.SVG}:
        raise VisualizationRenderingError(f"unsupported render format: {output_format.value}")
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        from matplotlib import pyplot as plt

        width = artifact.specification.width / 120
        height = artifact.specification.height / 120
        fig, ax = plt.subplots(figsize=(width, height), dpi=120)
        _draw(ax, artifact)
        ax.set_title(artifact.specification.title or artifact.visualization_type.value)
        if "x" in artifact.axis_metadata:
            ax.set_xlabel(_axis_label(artifact.axis_metadata["x"]))
        if "y" in artifact.axis_metadata:
            ax.set_ylabel(_axis_label(artifact.axis_metadata["y"]))
        ax.grid(True, linewidth=0.4, alpha=0.35)
        fig.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, format=output_format.value, metadata={"Creator": "polaris"})
        plt.close(fig)
        return output_path
    except Exception as exc:
        raise VisualizationRenderingError("failed to render visualization") from exc


def _draw(ax: Any, artifact: VisualizationArtifact) -> None:
    kind = artifact.visualization_type
    rows = list(artifact.plotting_data)
    if kind in {VisualizationType.COUNTRY_TIME_SERIES, VisualizationType.MULTI_COUNTRY_TREND}:
        _draw_trend(ax, rows)
    elif kind in {VisualizationType.SCATTERPLOT, VisualizationType.REGRESSION_RELATIONSHIP}:
        _draw_scatter(ax, rows)
    elif kind in {
        VisualizationType.COEFFICIENT_PLOT,
        VisualizationType.MODEL_COMPARISON,
        VisualizationType.CAUSAL_ESTIMATE,
        VisualizationType.ROBUSTNESS_ESTIMATES,
        VisualizationType.LEAVE_ONE_OUT,
        VisualizationType.PLACEBO,
    }:
        _draw_estimates(ax, rows)
    elif kind is VisualizationType.EVENT_STUDY:
        _draw_event_study(ax, rows)
    elif kind is VisualizationType.CORRELATION_MATRIX:
        _draw_correlation(ax, rows)
    elif kind in {
        VisualizationType.MISSINGNESS_BY_VARIABLE,
        VisualizationType.MISSINGNESS_BY_YEAR,
        VisualizationType.MISSINGNESS_BY_ENTITY,
        VisualizationType.PANEL_DIAGNOSTIC,
    }:
        _draw_bars(ax, rows)
    elif kind is VisualizationType.COUNTRY_YEAR_COVERAGE:
        _draw_coverage(ax, rows)
    elif kind is VisualizationType.DISTRIBUTION_HISTOGRAM:
        ax.hist([row["value"] for row in rows], bins=min(10, max(1, len(rows))))
    elif kind is VisualizationType.DISTRIBUTION_BOX:
        ax.boxplot([row["value"] for row in rows], vert=True)
    elif kind is VisualizationType.CAUSAL_STUDY_DIAGNOSTIC:
        _draw_causal_study(ax, rows)
    for line in artifact.specification.reference_lines:
        if line.orientation.value == "x":
            ax.axvline(line.value, color="black", linestyle="--", linewidth=1)
        else:
            ax.axhline(line.value, color="black", linestyle="--", linewidth=1)


def _draw_trend(ax: Any, rows: list[dict[str, Any]]) -> None:
    markers = ("o", "s", "^", "D", "v", "P", "X", "*")
    for index, entity in enumerate(sorted({row["entity"] for row in rows})):
        series = [row for row in rows if row["entity"] == entity and row.get("value") is not None]
        ax.plot(
            [row["year"] for row in series],
            [row["value"] for row in series],
            marker=markers[index % len(markers)],
            linewidth=1.6,
            label=str(entity),
        )
    if len({row["entity"] for row in rows}) > 1:
        ax.legend(loc="best", fontsize=8)


def _draw_scatter(ax: Any, rows: list[dict[str, Any]]) -> None:
    points = [row for row in rows if row.get("series") != "existing_ols_fitted_line"]
    ax.scatter([row["x"] for row in points], [row["y"] for row in points], s=28, alpha=0.85)
    fit = [row for row in rows if row.get("series") == "existing_ols_fitted_line"]
    if fit:
        fit = sorted(fit, key=lambda row: row["x"])
        ax.plot([row["x"] for row in fit], [row["y"] for row in fit], color="black", linewidth=1.4)


def _draw_estimates(ax: Any, rows: list[dict[str, Any]]) -> None:
    labels = [
        str(
            row.get("term")
            or row.get("model_id")
            or row.get("variant_id")
            or row.get("omitted_entity")
            or row.get("estimand")
            or index
        )
        for index, row in enumerate(rows)
    ]
    y = list(range(len(rows)))
    estimates = [row.get("estimate") for row in rows]
    for index, estimate in enumerate(estimates):
        if estimate is None:
            ax.scatter([0], [index], marker="x", color="red")
            continue
        low = rows[index].get("confidence_interval_low")
        high = rows[index].get("confidence_interval_high")
        if low is not None and high is not None:
            ax.errorbar(estimate, index, xerr=[[estimate - low], [high - estimate]], fmt="o")
        else:
            ax.scatter([estimate], [index])
    baseline_values = [
        row.get("baseline_estimate") for row in rows if row.get("baseline_estimate") is not None
    ]
    if baseline_values:
        ax.axvline(baseline_values[0], color="black", linestyle=":", linewidth=1)
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)


def _draw_event_study(ax: Any, rows: list[dict[str, Any]]) -> None:
    valid = [
        row for row in rows if row.get("estimate") is not None and not row.get("reference_period")
    ]
    ax.axhline(0, color="black", linestyle="--", linewidth=1)
    ax.axvline(0, color="black", linestyle=":", linewidth=1)
    for row in valid:
        estimate = row["estimate"]
        low = row.get("confidence_interval_low")
        high = row.get("confidence_interval_high")
        if low is not None and high is not None:
            ax.errorbar(
                row["event_time"], estimate, yerr=[[estimate - low], [high - estimate]], fmt="o"
            )
        else:
            ax.scatter([row["event_time"]], [estimate])
    ax.set_xticks([row["event_time"] for row in rows])


def _draw_correlation(ax: Any, rows: list[dict[str, Any]]) -> None:
    variables = sorted({row["variable_1"] for row in rows} | {row["variable_2"] for row in rows})
    values = [[1.0 if left == right else None for left in variables] for right in variables]
    for row in rows:
        i = variables.index(row["variable_1"])
        j = variables.index(row["variable_2"])
        values[i][j] = row["correlation"]
        values[j][i] = row["correlation"]
    matrix = [[0 if value is None else value for value in line] for line in values]
    image = ax.imshow(matrix, vmin=-1, vmax=1, cmap="coolwarm")
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(variables)))
    ax.set_yticks(range(len(variables)))
    ax.set_xticklabels(variables, rotation=45, ha="right")
    ax.set_yticklabels(variables)


def _draw_bars(ax: Any, rows: list[dict[str, Any]]) -> None:
    labels = [
        str(
            row.get("variable")
            or row.get("year")
            or row.get("entity")
            or row.get("variable_id")
            or index
        )
        for index, row in enumerate(rows)
    ]
    values = [
        row.get(
            "missing_rate", row.get("within_entity_standard_deviation", row.get("included_rows", 0))
        )
        or 0
        for row in rows
    ]
    ax.bar(labels, values)
    ax.tick_params(axis="x", labelrotation=45)


def _draw_coverage(ax: Any, rows: list[dict[str, Any]]) -> None:
    entities = sorted({row["entity"] for row in rows})
    years = sorted({row["year"] for row in rows})
    matrix = [
        [
            1
            if any(
                row["entity"] == entity and row["year"] == year and row["covered"] for row in rows
            )
            else 0
            for year in years
        ]
        for entity in entities
    ]
    ax.imshow(matrix, aspect="auto", vmin=0, vmax=1, cmap="Greys")
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, rotation=45, ha="right")
    ax.set_yticks(range(len(entities)))
    ax.set_yticklabels(entities)


def _draw_causal_study(ax: Any, rows: list[dict[str, Any]]) -> None:
    labels = [f"{row['entity']} ({row['role']})" for row in rows]
    starts = [row.get("treatment_start_period") or 0 for row in rows]
    ax.scatter(starts, range(len(rows)))
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels)


def _axis_label(axis: Any) -> str:
    if axis.unit:
        return f"{axis.label} ({axis.unit})"
    return axis.label
