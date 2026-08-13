"""Deterministic standalone HTML renderer for Phase 9 reports."""

from html import escape

from polaris.reporting.errors import ReportRenderingError
from polaris.reporting.markdown import render_report_markdown
from polaris.reporting.models import ResearchReport


def render_report_html(report: ResearchReport) -> str:
    try:
        markdown = render_report_markdown(report)
        body = _markdown_subset_to_html(markdown)
        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8">',
                "  <title>" + escape(report.title) + "</title>",
                "  <style>",
                "    body { font-family: system-ui, sans-serif; line-height: 1.5; margin: 2rem; }",
                "    table { border-collapse: collapse; width: 100%; margin: 1rem 0; }",
                "    th, td { border: 1px solid #d0d7de; padding: 0.35rem 0.5rem; }",
                "    th { background: #f6f8fa; text-align: left; }",
                "    code { background: #f6f8fa; padding: 0.1rem 0.2rem; }",
                "  </style>",
                "</head>",
                "<body>",
                body,
                "</body>",
                "</html>",
                "",
            ]
        )
    except Exception as exc:
        raise ReportRenderingError("failed to render report as HTML") from exc


def _markdown_subset_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html_lines: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            html_lines.append(f"<h1>{escape(line[2:])}</h1>")
            index += 1
            continue
        if line.startswith("## "):
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
            index += 1
            continue
        if line.startswith("### "):
            html_lines.append(f"<h3>{escape(line[4:])}</h3>")
            index += 1
            continue
        if line.startswith("- "):
            html_lines.append(f"<p>{escape(line)}</p>")
            index += 1
            continue
        if line.startswith("| "):
            table_lines = []
            while index < len(lines) and lines[index].startswith("| "):
                table_lines.append(lines[index])
                index += 1
            html_lines.append(_table_to_html(table_lines))
            continue
        html_lines.append(f"<p>{escape(line)}</p>")
        index += 1
    return "\n".join(html_lines)


def _table_to_html(lines: list[str]) -> str:
    if len(lines) < 2:
        return ""
    headers = _split_row(lines[0])
    body_rows = [_split_row(line) for line in lines[2:]]
    html = ["<table>", "<thead><tr>"]
    html.extend(f"<th>{escape(header)}</th>" for header in headers)
    html.append("</tr></thead>")
    html.append("<tbody>")
    for row in body_rows:
        html.append("<tr>")
        html.extend(f"<td>{escape(cell)}</td>" for cell in row)
        html.append("</tr>")
    html.append("</tbody></table>")
    return "\n".join(html)


def _split_row(line: str) -> list[str]:
    return [cell.strip().replace("\\|", "|") for cell in line.strip().strip("|").split("|")]
