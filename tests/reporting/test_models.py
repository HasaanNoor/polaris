import json

import pytest
from pydantic import ValidationError

from polaris.reporting.models import ReportFormat, ReportRequest
from polaris.reporting.service import build_research_report


def test_valid_report_request(report_request):
    assert report_request.output_format is ReportFormat.MARKDOWN


def test_request_rejects_unknown_fields(report_request):
    payload = report_request.model_dump(mode="python")
    payload["unknown"] = "field"
    with pytest.raises(ValidationError):
        ReportRequest.model_validate(payload)


def test_research_report_is_frozen(report_request):
    report = build_research_report(
        request=report_request, generation_timestamp="2026-07-28T00:00:00Z"
    )
    with pytest.raises(ValidationError):
        report.title = "changed"


def test_json_serialization_and_deterministic_id(report_request):
    report_a = build_research_report(
        request=report_request, generation_timestamp="2026-07-28T00:00:00Z"
    )
    report_b = build_research_report(
        request=report_request, generation_timestamp="2026-07-29T00:00:00Z"
    )
    assert report_a.report_id == report_b.report_id
    parsed = json.loads(report_a.model_dump_json())
    assert parsed["report_id"].startswith("report_")
