from polaris.reporting.html import render_report_html
from polaris.reporting.service import build_research_report


def test_html_rendering(report_request):
    report = build_research_report(request=report_request)
    html = render_report_html(report)
    assert html.startswith("<!doctype html>")
    assert "<h1>" in html
    assert "<h2>Limitations</h2>" in html
    assert "<table>" in html
    assert "<script" not in html.lower()
    assert "http://" not in html and "https://" not in html
    assert html == render_report_html(report)


def test_html_escapes_content(report_request):
    request = report_request.model_copy(update={"report_title": "Report <unsafe>"})
    html = render_report_html(build_research_report(request=request))
    assert "Report &lt;unsafe&gt;" in html
    assert "Report <unsafe>" not in html
