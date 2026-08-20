"""Deterministic Markdown renderer for Phase 9 reports."""

from collections.abc import Iterable, Sequence
from typing import Any

from polaris.reporting.errors import ReportRenderingError
from polaris.reporting.models import ResearchReport


def render_report_markdown(report: ResearchReport) -> str:
    try:
        lines: list[str] = []
        lines.extend([f"# {_md(report.title)}", ""])
        if report.subtitle:
            lines.extend([_md(report.subtitle), ""])
        lines.extend(
            [
                "## Metadata",
                "",
                _table(
                    ("Field", "Value"),
                    (
                        ("Report ID", report.report_id),
                        ("Generated", report.report_metadata.generation_timestamp.isoformat()),
                        ("Dataset ID", report.report_metadata.dataset_id),
                        ("Source checksum", report.report_metadata.source_checksum_sha256),
                        ("Analysis procedure", report.report_metadata.analysis_procedure.value),
                        ("Synthesis mode", report.report_metadata.synthesis_mode.value),
                        ("Ruleset", report.report_metadata.deterministic_ruleset_version),
                    ),
                ),
                "",
                "## Executive Summary",
                "",
                _md(report.executive_summary),
                "",
                "## Research Question",
                "",
            ]
        )
        rq = report.research_question_section
        if rq.status.value == "unavailable":
            lines.extend(["Research question metadata is unavailable.", ""])
        else:
            lines.extend(
                [
                    _table(
                        ("Field", "Value"),
                        (
                            ("Question ID", rq.question_id),
                            ("Primary question", rq.primary_question),
                            ("Population", rq.population),
                            ("Variables", ", ".join(rq.variables_or_concepts)),
                            ("Methods", ", ".join(rq.intended_analytical_methods)),
                        ),
                    ),
                    "",
                ]
            )
        ds = report.dataset_section
        lines.extend(
            [
                "## Dataset and Source",
                "",
                _table(
                    ("Field", "Value"),
                    (
                        ("Dataset ID", ds.dataset_id),
                        ("Title", ds.dataset_title),
                        ("Provider", ds.provider),
                        ("Source type", ds.source_type),
                        ("Checksum", ds.source_checksum_sha256),
                        ("Accepted rows", ds.accepted_row_count),
                        ("Rejected rows", ds.rejected_row_count),
                        ("Analysis ready", ds.analysis_ready),
                        ("Illustrative", ds.illustrative),
                        ("Variables", ", ".join(ds.relevant_variable_ids)),
                    ),
                ),
                "",
                "## Methodology",
                "",
                _table(
                    ("Field", "Value"),
                    (
                        (
                            "Ingestion and validation",
                            report.methodology_section.ingestion_and_validation,
                        ),
                        ("Sample construction", report.methodology_section.sample_construction),
                        ("Procedure", report.methodology_section.statistical_procedure.value),
                        ("Dependent variable", report.methodology_section.dependent_variable),
                        ("Predictors", ", ".join(report.methodology_section.predictors)),
                        ("Controls", ", ".join(report.methodology_section.controls)),
                        ("Include intercept", report.methodology_section.include_intercept),
                        ("Confidence level", report.methodology_section.confidence_level),
                        (
                            "Significance threshold",
                            report.methodology_section.significance_threshold,
                        ),
                        (
                            "Diagnostics calculated",
                            ", ".join(report.methodology_section.diagnostics_calculated),
                        ),
                        (
                            "Evidence extraction",
                            report.methodology_section.evidence_extraction_process,
                        ),
                        ("Domain agents", report.methodology_section.domain_agent_process),
                        ("Coordination", report.methodology_section.coordination_process),
                        ("Synthesis mode", report.methodology_section.synthesis_mode.value),
                        (
                            "Grounding and validation",
                            report.methodology_section.grounding_and_validation,
                        ),
                    ),
                ),
                "",
                "## Statistical Results",
                "",
            ]
        )
        lines.extend(_statistical_results(report))
        lines.extend(_causal_design(report))
        lines.extend(
            [
                "## Evidence and Claims",
                "",
                _table(
                    ("Evidence ID", "Type", "Variables", "Direction", "Limitations"),
                    (
                        (
                            item.evidence_id,
                            item.evidence_type,
                            ", ".join(item.variable_ids),
                            item.direction,
                            ", ".join(code.value for code in item.limitation_codes),
                        )
                        for item in report.evidence_section.evidence_records
                    ),
                ),
                "",
                _table(
                    ("Claim ID", "Type", "Evidence IDs", "Direction", "Causal", "Scope"),
                    (
                        (
                            item.claim_id,
                            item.claim_type,
                            ", ".join(item.supporting_evidence_ids),
                            item.direction,
                            item.causal,
                            item.generalization_scope,
                        )
                        for item in report.evidence_section.claim_candidates
                    ),
                ),
                "",
                "## Domain Assessments",
                "",
                _table(
                    ("Domain", "Supplied", "Coverage", "Evidence", "Claims", "Unsupported"),
                    (
                        (
                            item.domain.value,
                            item.assessment_supplied,
                            item.coverage_status.value,
                            item.relevant_evidence_count,
                            item.relevant_claim_count,
                            ", ".join(code.value for code in item.unsupported_inferences),
                        )
                        for item in report.domain_assessments_section.domains
                    ),
                ),
                "",
                "## Cross-Domain Synthesis",
                "",
                _md(report.synthesis_section.overall_summary),
                "",
            ]
        )
        if report.cross_domain_section.cross_domain_findings:
            lines.extend(
                [
                    _table(
                        ("Finding ID", "Domains", "Claim IDs", "Evidence IDs"),
                        (
                            (
                                item["finding_id"],
                                ", ".join(item["domains"]),
                                ", ".join(item.get("referenced_claim_ids", ())),
                                ", ".join(item.get("referenced_evidence_ids", ())),
                            )
                            for item in report.cross_domain_section.cross_domain_findings
                        ),
                    ),
                    "",
                ]
            )
        lines.extend(_evidence_grounded_interpretation(report))
        lines.extend(
            [
                "## Phase 8 Synthesis",
                "",
                _md(report.synthesis_section.overall_summary),
                "",
                _table(
                    ("Domain", "Summary", "Claims", "Evidence"),
                    (
                        (
                            item["domain"],
                            item["summary"],
                            ", ".join(item.get("referenced_claim_ids", ())),
                            ", ".join(item.get("referenced_evidence_ids", ())),
                        )
                        for item in report.synthesis_section.domain_summaries
                    ),
                ),
                "",
            ]
        )
        lines.extend(_literature_context(report))
        lines.extend(
            [
                "## Limitations",
                "",
                _md(report.limitations_section.narrative_summary),
                "",
                _table(
                    ("Limitation Code",),
                    ((code.value,) for code in report.limitations_section.limitation_codes),
                ),
                "",
                "## Evidence and Domain Gaps",
                "",
                _table(
                    ("Gap ID", "Type", "Sources", "Domains"),
                    (
                        (
                            item["gap_id"],
                            item["gap_type"],
                            ", ".join(item.get("source_ids", ())),
                            ", ".join(item.get("domains", ())),
                        )
                        for item in report.gaps_section.evidence_gaps
                    ),
                ),
                "",
                _table(
                    ("Gap ID", "Type", "Domain", "Assessment supplied"),
                    (
                        (
                            item["gap_id"],
                            item["gap_type"],
                            item["domain"],
                            item["assessment_supplied"],
                        )
                        for item in report.gaps_section.domain_gaps
                    ),
                ),
                "",
                "## Unsupported Inferences",
                "",
                _table(
                    ("Boundary",),
                    (
                        (code.value,)
                        for code in report.unsupported_inferences_section.unsupported_inferences
                    ),
                ),
                "",
                "## Provenance",
                "",
                _table(
                    ("Stage", "Identifier"),
                    (
                        ("Source dataset", report.provenance_section.dataset_id),
                        ("Phase 3 DatasetIngestionResult", report.provenance_section.dataset_id),
                        ("Phase 4 AnalysisResult", report.provenance_section.analysis_result_id),
                        (
                            "Phase 5 EvidenceArtifact",
                            report.provenance_section.evidence_artifact_id,
                        ),
                        (
                            "Phase 6 AgentAssessments",
                            ", ".join(report.provenance_section.agent_assessment_ids),
                        ),
                        (
                            "Phase 7 CoordinatedAssessment",
                            report.provenance_section.coordinated_assessment_id,
                        ),
                        (
                            "Phase 8 SynthesisArtifact",
                            report.provenance_section.synthesis_artifact_id,
                        ),
                        ("Phase 9 ResearchReport", report.provenance_section.report_id),
                    ),
                ),
                "",
                "## Reference Index",
                "",
                _table(
                    ("Reference ID", "Kind", "Label"),
                    (
                        (item.reference_id, item.reference_kind.value, item.label)
                        for item in report.reference_index
                    ),
                ),
            ]
        )
        return "\n".join(lines).rstrip() + "\n"
    except Exception as exc:
        raise ReportRenderingError("failed to render report as Markdown") from exc


def _literature_context(report: ResearchReport) -> list[str]:
    section = report.literature_context_section
    if section is None or section.status.value != "available":
        return []
    rows = []
    for record in section.records:
        chunks = record.get("chunks", [])
        top = chunks[0] if chunks else {}
        citation = " ".join(
            str(part)
            for part in (
                ", ".join(top.get("authors", ())),
                top.get("year"),
                top.get("title"),
            )
            if part
        )
        rows.append(
            (
                record["empirical_claim_id"],
                record["retrieval_query"],
                record["support_classification"],
                top.get("chunk_id"),
                top.get("score"),
                citation,
            )
        )
    summary = section.retrieval_summary
    return [
        "## Literature Context",
        "",
        _table(
            ("Field", "Value"),
            (
                ("Literature context ID", section.literature_context_id),
                ("Corpus ID", section.corpus_id),
                ("Documents", summary.get("corpus_document_count")),
                ("Chunks", summary.get("chunk_count")),
                ("Queries", summary.get("query_count")),
                ("Unmatched claims", ", ".join(section.unmatched_claims)),
            ),
        ),
        "",
        _table(
            ("Claim ID", "Query", "Class", "Top chunk", "Score", "Citation"),
            rows,
        ),
        "",
        "Literature context is retrieved from the supplied corpus and does not change "
        "the empirical findings.",
        "",
    ]


def _causal_design(report: ResearchReport) -> list[str]:
    section = report.causal_design_section
    if section is None or section.status.value != "available":
        return []
    lines = [
        "## Causal Design",
        "",
        _table(
            ("Field", "Value"),
            (
                ("Research design", section.research_design),
                ("Treatment", section.treatment),
                ("Comparison group", section.comparison_group),
                ("Treatment timing", section.treatment_timing),
                ("Outcome", section.outcome),
                ("Estimand", section.estimand),
                ("Model", section.model),
                ("Treatment effect", section.treatment_effect),
                ("Clustered uncertainty", section.clustered_uncertainty),
                ("Registry provenance", section.registry_provenance or None),
            ),
        ),
        "",
        "### Identifying Assumptions",
        "",
        _table(
            ("Assumption", "Status", "Diagnostic Evidence", "Limitation"),
            (
                (
                    item.get("assumption_code"),
                    item.get("status"),
                    item.get("diagnostic_evidence"),
                    item.get("limitation"),
                )
                for item in section.identifying_assumptions
            ),
        ),
        "",
        "### Causal Diagnostics",
        "",
        _table(
            ("Diagnostic", "Status", "Summary"),
            (
                (
                    item.get("diagnostic_type"),
                    item.get("status"),
                    item.get("diagnostic_summary"),
                )
                for item in section.diagnostics
            ),
        ),
        "",
    ]
    return lines


def _evidence_grounded_interpretation(report: ResearchReport) -> list[str]:
    section = report.evidence_grounded_interpretation_section
    if section is None:
        return []
    lines = ["## Evidence-Grounded Interpretation", ""]
    groups = (
        ("Main interpretation", section.main_interpretations),
        ("Cross-domain patterns", section.cross_domain_patterns),
        ("Plausible mechanisms", section.plausible_mechanisms),
        ("Alternative explanations", section.alternative_explanations),
        ("Potential confounders", section.potential_confounders),
        ("Contradictions", section.contradictions),
        ("Limitations", section.limitations),
        ("Follow-up hypotheses", section.follow_up_hypotheses),
        ("Follow-up research questions", section.follow_up_research_questions),
    )
    for title, rows in groups:
        if not rows:
            continue
        lines.extend([f"### {title}", ""])
        for row in rows:
            if "text" in row:
                label = row.get("category", title)
                status = row.get("epistemic_status", "")
                text = row["text"]
                ids = ", ".join(
                    [
                        *row.get("claim_ids", ()),
                        *row.get("evidence_ids", ()),
                        *row.get("literature_evidence_ids", ()),
                    ]
                )
                lines.append(f"- **{_md(str(label))}** ({_md(str(status))}): {_md(text)}")
                if ids:
                    lines.append(f"  References: {_md(ids)}")
            elif "variable_or_concept" in row:
                lines.append(
                    "- **"
                    + _md(row["variable_or_concept"])
                    + "**: "
                    + _md(row["reason_it_may_matter"])
                )
            elif "nature_of_conflict" in row:
                lines.append(
                    "- **Unresolved conflict**: "
                    + _md(row["nature_of_conflict"])
                    + " "
                    + _md(row["possible_explanation"])
                )
        lines.append("")
    return lines


def _statistical_results(report: ResearchReport) -> list[str]:
    section = report.statistical_results_section
    lines = [
        _table(
            ("Field", "Value"),
            (
                ("Analysis result ID", section.analysis_result_id),
                ("Method", section.method.value),
                ("Sample size", section.sample_size),
            ),
        ),
        "",
    ]
    if section.descriptive_results:
        lines.extend(
            [
                _table(
                    ("Variable", "Type", "Count", "Missing", "Mean", "Minimum", "Maximum"),
                    (
                        (
                            item["variable_id"],
                            item["variable_type"],
                            _nested(item, "numeric", "count")
                            or _nested(item, "categorical", "count"),
                            _nested(item, "numeric", "missing_count")
                            or _nested(item, "categorical", "missing_count"),
                            _nested(item, "numeric", "mean"),
                            _nested(item, "numeric", "minimum"),
                            _nested(item, "numeric", "maximum"),
                        )
                        for item in section.descriptive_results
                    ),
                ),
                "",
            ]
        )
    if section.correlation_results:
        lines.extend(
            [
                _table(
                    (
                        "Variable 1",
                        "Variable 2",
                        "Method",
                        "N",
                        "Coefficient",
                        "p-value",
                        "Defined",
                    ),
                    (
                        (
                            item["variable_id_1"],
                            item["variable_id_2"],
                            item["method"],
                            item["observation_count"],
                            item["correlation_coefficient"],
                            item["p_value"],
                            item["defined"],
                        )
                        for item in section.correlation_results
                    ),
                ),
                "",
            ]
        )
    if section.regression_results:
        result = section.regression_results
        lines.extend(
            [
                _table(
                    ("Term", "Estimate", "Std. Error", "Statistic", "p-value", "CI Low", "CI High"),
                    (
                        (
                            item["term"],
                            item["estimate"],
                            item["standard_error"],
                            item["test_statistic"],
                            item["p_value"],
                            item["confidence_interval_low"],
                            item["confidence_interval_high"],
                        )
                        for item in result["coefficients"]
                    ),
                ),
                "",
                _table(
                    ("Metric", "Value"),
                    (
                        ("R-squared", result["r_squared"]),
                        ("Adjusted R-squared", result["adjusted_r_squared"]),
                        ("Residual degrees of freedom", result["residual_degrees_of_freedom"]),
                        ("Model degrees of freedom", result["model_degrees_of_freedom"]),
                        ("RSS", result["residual_sum_of_squares"]),
                        ("MSE", result["mean_squared_error"]),
                    ),
                ),
                "",
            ]
        )
    return lines


def _table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    rendered_rows = [tuple(_cell(value) for value in row) for row in rows]
    if not rendered_rows:
        rendered_rows = [tuple("" for _ in headers)]
    header = "| " + " | ".join(_md(header) for header in headers) + " |"
    divider = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rendered_rows]
    return "\n".join([header, divider, *body])


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return _md(str(value))


def _md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _nested(item: dict[str, Any], *path: str) -> Any:
    current: Any = item
    for key in path:
        if current is None:
            return None
        current = current.get(key)
    return current
