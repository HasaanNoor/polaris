from pathlib import Path

from polaris.projects import plan_research_project
from polaris.projects.models import ResearchStage
from tests.projects.helpers import harmonized_project, single_manifest_project


def test_single_dataset_plan_skips_harmonization(tmp_path: Path) -> None:
    plan = plan_research_project(single_manifest_project(tmp_path))

    assert plan.harmonization_required is False
    assert ResearchStage.HARMONIZE not in plan.stages
    assert plan.stages == (
        ResearchStage.RESOLVE_DATASETS,
        ResearchStage.INGEST,
        ResearchStage.ANALYZE,
        ResearchStage.EXTRACT_EVIDENCE,
        ResearchStage.RUN_AGENTS,
        ResearchStage.COORDINATE,
        ResearchStage.SYNTHESIZE,
        ResearchStage.REPORT,
        ResearchStage.COMPLETE,
    )


def test_multi_dataset_plan_includes_harmonization(tmp_path: Path) -> None:
    plan = plan_research_project(harmonized_project(tmp_path))

    assert plan.harmonization_required is True
    assert ResearchStage.HARMONIZE in plan.stages
    assert plan.required_datasets == ("wdi", "who")


def test_equivalent_requests_get_same_project_id(tmp_path: Path) -> None:
    request = single_manifest_project(tmp_path)

    assert plan_research_project(request).project_id == plan_research_project(request).project_id


def test_selected_agent_order_is_deterministic(tmp_path: Path) -> None:
    plan = plan_research_project(single_manifest_project(tmp_path))

    assert [agent.value for agent in plan.selected_agents] == ["economics", "public_health"]
