from polaris.reporting.models import ReportFormat
from polaris.reporting.service import generate_report, report_to_json


def test_generate_report_markdown(report_request):
    generated = generate_report(request=report_request)
    assert generated.output_format is ReportFormat.MARKDOWN
    assert generated.report.report_id
    assert generated.rendered_content is not None
    assert "## Reference Index" in generated.rendered_content


def test_generate_report_json(report_request):
    request = report_request.model_copy(update={"output_format": ReportFormat.JSON})
    generated = generate_report(request=request)
    assert generated.rendered_content is not None
    assert '"report_id"' in generated.rendered_content
    assert report_to_json(generated.report).startswith("{")


def test_generate_report_html(report_request):
    request = report_request.model_copy(update={"output_format": ReportFormat.HTML})
    generated = generate_report(request=request)
    assert generated.rendered_content is not None
    assert generated.rendered_content.startswith("<!doctype html>")
