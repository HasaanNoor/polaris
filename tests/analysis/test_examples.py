from pathlib import Path

from polaris.schemas.statistics import StatisticalSpecification


def test_example_analysis_specifications_validate():
    for path in sorted((Path("examples") / "analysis").glob("*.json")):
        StatisticalSpecification.model_validate_json(path.read_text(encoding="utf-8"))
