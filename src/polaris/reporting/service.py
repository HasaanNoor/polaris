"""Public API for Phase 9 structured research report generation."""

import json
from datetime import UTC, datetime

from polaris.evidence.provenance import deterministic_id
from polaris.reporting.errors import ReportGenerationError, UnsupportedReportFormatError
from polaris.reporting.html import render_report_html
from polaris.reporting.markdown import render_report_markdown
from polaris.reporting.models import (
    REPORT_RULESET_VERSION,
    REPORT_SCHEMA_VERSION,
    GeneratedReport,
    ReportFormat,
    ReportMetadata,
    ReportRequest,
    ResearchReport,
)
from polaris.reporting.references import build_reference_index
from polaris.reporting.sections import (
    cross_domain_section,
    dataset_section,
    domain_assessments_section,
    evidence_section,
    executive_summary,
    gaps_section,
    limitations_section,
    methodology_section,
    provenance_section,
    research_question_section,
    statistical_results_section,
    synthesis_section,
    unsupported_inferences_section,
)
from polaris.reporting.validation import validate_report, validate_report_request


def generate_report(
    *,
    request: ReportRequest,
    generation_timestamp: datetime | None = None,
) -> GeneratedReport:
    """Generate a structured Phase 9 report and optional rendered output."""

    try:
        validate_report_request(request)
        timestamp = generation_timestamp or datetime.now(UTC)
        report = build_research_report(request=request, generation_timestamp=timestamp)
        validate_report(report, request)
        rendered = render_report(report, request.output_format)
        return GeneratedReport(
            report=report,
            rendered_content=rendered,
            output_format=request.output_format,
        )
    except ReportGenerationError:
        raise
    except Exception as exc:
        raise ReportGenerationError("failed to generate research report") from exc


def build_research_report(
    *, request: ReportRequest, generation_timestamp: datetime | None = None
) -> ResearchReport:
    """Build the structured report without rendering it."""

    validate_report_request(request)
    timestamp = generation_timestamp or datetime.now(UTC)
    title = request.report_title or _default_title(request)
    source_ids = _source_artifact_ids(request)
    report_id = _report_id(request, title=title)
    metadata = ReportMetadata(
        title=title,
        subtitle=request.report_subtitle,
        generation_timestamp=timestamp,
        dataset_id=request.ingestion_result.dataset_manifest.dataset_id,
        source_checksum_sha256=request.ingestion_result.checksum_sha256,
        analysis_procedure=request.analysis_result.analysis_method,
        synthesis_mode=request.synthesis_artifact.synthesis_mode,
        source_artifact_ids=source_ids,
        author=request.author,
        organization=request.organization,
        report_format=request.output_format,
    )
    report = ResearchReport(
        report_id=report_id,
        title=title,
        subtitle=request.report_subtitle,
        report_metadata=metadata,
        executive_summary=executive_summary(
            request.synthesis_artifact, request.coordinated_assessment
        ),
        research_question_section=research_question_section(request.research_question),
        dataset_section=dataset_section(
            ingestion_result=request.ingestion_result,
            manifest=request.dataset_manifest,
            analysis_result=request.analysis_result,
        ),
        methodology_section=methodology_section(
            analysis_result=request.analysis_result,
            evidence_artifact=request.evidence_artifact,
            coordinated_assessment=request.coordinated_assessment,
            synthesis_artifact=request.synthesis_artifact,
        ),
        statistical_results_section=statistical_results_section(request.analysis_result),
        evidence_section=evidence_section(request.evidence_artifact),
        domain_assessments_section=domain_assessments_section(request.coordinated_assessment),
        cross_domain_section=cross_domain_section(
            coordinated_assessment=request.coordinated_assessment,
            synthesis_artifact=request.synthesis_artifact,
        ),
        synthesis_section=synthesis_section(request.synthesis_artifact),
        limitations_section=limitations_section(
            evidence_artifact=request.evidence_artifact,
            analysis_result=request.analysis_result,
            coordinated_assessment=request.coordinated_assessment,
            synthesis_artifact=request.synthesis_artifact,
        ),
        gaps_section=gaps_section(request.coordinated_assessment),
        unsupported_inferences_section=unsupported_inferences_section(
            request.coordinated_assessment, request.synthesis_artifact
        ),
        provenance_section=provenance_section(
            ingestion_result=request.ingestion_result,
            analysis_result=request.analysis_result,
            evidence_artifact=request.evidence_artifact,
            coordinated_assessment=request.coordinated_assessment,
            synthesis_artifact=request.synthesis_artifact,
            report_id=report_id,
            generation_timestamp=timestamp,
            report_ruleset_version=REPORT_RULESET_VERSION,
        ),
        reference_index=build_reference_index(
            evidence_artifact=request.evidence_artifact,
            coordinated_assessment=request.coordinated_assessment,
            source_artifact_ids=source_ids,
        ),
        source_artifact_ids=source_ids,
    )
    validate_report(report, request)
    return report


def render_report(report: ResearchReport, output_format: ReportFormat) -> str | None:
    if output_format is ReportFormat.JSON:
        return report.model_dump_json(indent=2)
    if output_format is ReportFormat.MARKDOWN:
        return render_report_markdown(report)
    if output_format is ReportFormat.HTML:
        return render_report_html(report)
    raise UnsupportedReportFormatError(f"unsupported report format: {output_format}")


def report_to_json(report: ResearchReport) -> str:
    return json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2, allow_nan=False)


def _report_id(request: ReportRequest, *, title: str) -> str:
    return deterministic_id(
        "report_",
        {
            "source_synthesis_artifact_id": request.synthesis_artifact.synthesis_id,
            "source_coordinated_assessment_id": (
                request.coordinated_assessment.coordinated_assessment_id
            ),
            "source_evidence_artifact_id": request.evidence_artifact.artifact_id,
            "report_format": request.output_format.value,
            "report_ruleset_version": REPORT_RULESET_VERSION,
            "report_schema_version": REPORT_SCHEMA_VERSION,
            "title": title,
            "subtitle": request.report_subtitle,
            "author": request.author,
            "organization": request.organization,
        },
    )


def _default_title(request: ReportRequest) -> str:
    if request.research_question is not None:
        return request.research_question.raw_text
    return f"Structured Polaris Report for {request.ingestion_result.dataset_manifest.dataset_id}"


def _source_artifact_ids(request: ReportRequest) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                request.analysis_result.result_id,
                request.evidence_artifact.artifact_id,
                request.coordinated_assessment.coordinated_assessment_id,
                request.synthesis_artifact.synthesis_id,
                request.ingestion_result.dataset_manifest.dataset_id,
            }
        )
    )
