from pathlib import Path


def test_example_outputs_exist_and_are_illustrative():
    base = Path("examples/reporting")
    for name in ("research_report.json", "research_report.md", "research_report.html"):
        path = base / name
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "Illustrative" in text
