from polaris.reporting.markdown import render_report_markdown
from polaris.reporting.service import build_research_report


def test_markdown_rendering(report_request):
    report = build_research_report(request=report_request)
    markdown = render_report_markdown(report)
    assert markdown.startswith("# Illustrative Literacy")
    assert "## Limitations" in markdown
    assert "## Provenance" in markdown
    assert "| Evidence ID | Type |" in markdown
    assert "object at 0x" not in markdown
    assert "http://" not in markdown and "https://" not in markdown
    assert markdown == render_report_markdown(report)


def test_markdown_section_order(report_request):
    markdown = render_report_markdown(build_research_report(request=report_request))
    headings = [
        "## Executive Summary",
        "## Research Question",
        "## Dataset and Source",
        "## Methodology",
        "## Statistical Results",
        "## Evidence and Claims",
        "## Domain Assessments",
        "## Cross-Domain Synthesis",
        "## Phase 8 Synthesis",
        "## Limitations",
        "## Evidence and Domain Gaps",
        "## Unsupported Inferences",
        "## Provenance",
        "## Reference Index",
    ]
    positions = [markdown.index(heading) for heading in headings]
    assert positions == sorted(positions)
