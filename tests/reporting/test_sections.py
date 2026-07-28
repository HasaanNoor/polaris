from polaris.reporting.models import ReportFormat, ReportRequest, SectionStatus
from polaris.reporting.service import build_research_report


def test_sections_present(report_request):
    report = build_research_report(request=report_request)
    assert report.research_question_section.status is SectionStatus.AVAILABLE
    assert report.dataset_section.accepted_row_count > 0
    assert report.methodology_section.statistical_procedure.value == "ordinary_least_squares"
    assert report.statistical_results_section.regression_results is not None
    assert report.evidence_section.evidence_records
    assert report.evidence_section.claim_candidates
    assert len(report.domain_assessments_section.domains) == 4
    assert report.synthesis_section.synthesis_id == report_request.synthesis_artifact.synthesis_id
    assert report.limitations_section.limitation_codes
    assert report.unsupported_inferences_section.unsupported_inferences
    assert report.provenance_section.report_id == report.report_id
    assert report.reference_index


def test_research_question_absent(report_request):
    request = report_request.model_copy(update={"research_question": None})
    report = build_research_report(request=request)
    assert report.research_question_section.status is SectionStatus.UNAVAILABLE


def test_dataset_section_preserves_sample_status(report_request):
    report = build_research_report(request=report_request)
    assert report.dataset_section.illustrative is True
    assert report.dataset_section.source_type == "local_csv"
    assert (
        report.dataset_section.source_checksum_sha256
        == report_request.ingestion_result.checksum_sha256
    )


def test_output_format_changes_report_identity(report_request):
    md_report = build_research_report(request=report_request)
    html_request = report_request.model_copy(update={"output_format": ReportFormat.HTML})
    html_report = build_research_report(request=html_request)
    assert md_report.report_id != html_report.report_id


def test_descriptive_and_correlation_sections(reporting_pipeline):
    base = reporting_pipeline
    for method, expected_field in (
        ("descriptive_statistics", "descriptive_results"),
        ("pearson_correlation", "correlation_results"),
    ):
        from polaris.analysis.models import AnalysisRequest
        from polaris.analysis.service import run_analysis
        from polaris.evidence.service import extract_evidence
        from polaris.schemas.statistics import StatisticalSpecification

        payload = base["analysis"].statistical_specification.model_dump(mode="json")
        payload["procedure"] = method
        payload["analysis_type"] = (
            "descriptive" if method == "descriptive_statistics" else "correlation"
        )
        payload["model_family"] = "none"
        analysis = run_analysis(
            request=AnalysisRequest(
                ingestion_result=base["ingestion"],
                statistical_specification=StatisticalSpecification.model_validate(payload),
            )
        )
        evidence = extract_evidence(analysis_result=analysis)
        request = ReportRequest(
            synthesis_artifact=base["synthesis"],
            coordinated_assessment=base["coordinated"],
            evidence_artifact=base["evidence"],
            analysis_result=base["analysis"],
            ingestion_result=base["ingestion"],
        )
        report = build_research_report(request=request)
        assert getattr(report.statistical_results_section, expected_field) == ()
        assert evidence.artifact_id
