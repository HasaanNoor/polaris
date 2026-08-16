from __future__ import annotations

from examples.evaluation.benchmarks.baseline import baseline_suite
from polaris.evidence.service import extract_evidence
from polaris.literature.ingestion import ingest_literature_corpus
from polaris.mcp.config import MCPServerConfig
from polaris.mcp.tools import MCPToolService
from polaris.reasoning import ReasoningMode, ReasoningRequest, build_reasoning_artifact
from tests.analysis.helpers import make_spec
from tests.evidence.evidence_helpers import ingest_fixture, run_fixture_analysis
from tests.harmonization.helpers import request_for, wdi_result, who_result
from tests.projects.helpers import single_manifest_project


def test_list_datasets_valid_filters_no_results_and_determinism():
    service = MCPToolService()

    governance = service.call_tool("list_datasets", {"research_domain": "governance"})
    missing = service.call_tool("list_datasets", {"provider": "missing provider"})

    assert governance == service.call_tool("list_datasets", {"research_domain": "governance"})
    assert any("wgi" in item["dataset_id"] for item in governance["datasets"])
    assert missing["datasets"] == []


def test_inspect_dataset_valid_and_missing_id():
    service = MCPToolService()

    result = service.call_tool("inspect_dataset", {"dataset_id": "world_bank_wdi_illustrative"})
    missing = service.call_tool("inspect_dataset", {"dataset_id": "missing"})

    assert result["manifest"]["dataset_id"] == "world_bank_wdi_illustrative"
    assert missing["error"]["category"] in {"not_found", "execution"}


def test_run_analysis_requires_explicit_valid_specification(tmp_path):
    service = MCPToolService()
    ingestion = ingest_fixture(tmp_path)
    spec = make_spec(
        procedure="pearson_correlation",
        analysis_type="correlation",
        model_family="none",
        outcome="y",
        exposures=["x"],
    )

    valid = service.call_tool(
        "run_analysis",
        {
            "ingestion_result": ingestion.model_dump(mode="json"),
            "statistical_specification": spec.model_dump(mode="json"),
        },
    )
    invalid_spec = spec.model_dump(mode="json")
    invalid_spec["outcome_variable"] = {"variable_id": "missing"}
    missing_spec = service.call_tool(
        "run_analysis",
        {"ingestion_result": ingestion.model_dump(mode="json")},
    )
    invalid_variable = service.call_tool(
        "run_analysis",
        {
            "ingestion_result": ingestion.model_dump(mode="json"),
            "statistical_specification": invalid_spec,
        },
    )

    assert valid["artifact"]["artifact_type"] == "analysis_result"
    assert missing_spec["error"]["code"] == "validation_error"
    assert invalid_variable["error"]["category"] in {"validation", "execution"}


def test_integrate_datasets_requires_explicit_mappings(tmp_path):
    service = MCPToolService()
    wdi = wdi_result(tmp_path)
    who = who_result(tmp_path)
    request = request_for(wdi, who)

    valid = service.call_tool(
        "integrate_datasets",
        {"harmonization_request": request.model_dump(mode="json")},
    )
    missing_join = service.call_tool(
        "integrate_datasets",
        {
            "harmonization_request": {
                "ingestion_results": [wdi.model_dump(mode="json"), who.model_dump(mode="json")],
                "dataset_configs": [
                    item.model_dump(mode="json") for item in request.dataset_configs
                ],
                "variable_mappings": [
                    item.model_dump(mode="json") for item in request.variable_mappings
                ],
            }
        },
    )

    assert valid["artifact"]["artifact_type"] == "harmonized_dataset"
    assert missing_join["error"]["code"] == "validation_error"


def test_run_research_project_success_and_invalid_request(tmp_path):
    service = MCPToolService(
        config=MCPServerConfig(allowed_project_output_directory=tmp_path / "outputs")
    )
    request = single_manifest_project(tmp_path).model_copy(
        update={"output_directory": tmp_path / "outputs"}
    )

    valid = service.call_tool(
        "run_research_project",
        {"project_request": request.model_dump(mode="json")},
    )
    invalid = service.call_tool("run_research_project", {"project_request": {"project_name": ""}})

    assert valid["status"] == "completed"
    assert valid["artifact_ids"]["report_id"]
    assert invalid["error"]["code"] == "validation_error"


def test_retrieve_literature_uses_local_configured_corpus_only():
    corpus = ingest_literature_corpus(
        "examples/literature/corpus",
        manifest_path="examples/literature/corpus/manifest.json",
    )
    service = MCPToolService()

    valid = service.call_tool(
        "retrieve_literature",
        {
            "corpus_id": corpus.corpus_id,
            "corpus_path": "examples/literature/corpus",
            "query": "income health life expectancy",
            "top_k": 2,
        },
    )
    missing = service.call_tool(
        "retrieve_literature",
        {"corpus_id": "missing", "query": "income", "top_k": 1},
    )

    assert valid["artifact"]["artifact_type"] == "literature_retrieval"
    assert missing["error"]["category"] == "safety"


def test_run_reasoning_grounding_and_causal_guards(tmp_path):
    service = MCPToolService()
    analysis = run_fixture_analysis(
        ingest_fixture(tmp_path),
        procedure="ordinary_least_squares",
        analysis_type="regression",
        model_family="linear",
        outcome="y",
        exposures=["x"],
        covariates=["z"],
    )
    evidence = extract_evidence(analysis_result=analysis)
    case = baseline_suite().benchmark_cases[0]
    request = ReasoningRequest(
        research_question=case.research_question,
        evidence_artifact=case.evidence_artifact,
        coordinated_assessment=case.coordinated_assessment,
        literature_context=case.literature_context,
        mode=ReasoningMode.DETERMINISTIC,
    )

    valid = service.call_tool(
        "run_reasoning",
        {"reasoning_request": request.model_dump(mode="json")},
    )
    bad = service.call_tool(
        "run_reasoning",
        {
            "reasoning_request": {
                "research_question": "bad",
                "evidence_artifact": evidence.model_dump(mode="json"),
                "coordinated_assessment": case.coordinated_assessment.model_dump(mode="json"),
            }
        },
    )

    assert valid["artifact"]["artifact_type"] == "reasoning_artifact"
    assert bad["error"]["code"] == "validation_error"


def test_evaluate_reasoning_valid_and_adversarial_failure():
    service = MCPToolService()
    case = next(
        item for item in baseline_suite().benchmark_cases if item.case_id.startswith("case_c")
    )
    reasoning = build_reasoning_artifact(
        request=ReasoningRequest(
            research_question=case.research_question,
            evidence_artifact=case.evidence_artifact,
            coordinated_assessment=case.coordinated_assessment,
            literature_context=case.literature_context,
            mode=ReasoningMode.DETERMINISTIC,
        )
    )
    flawed = reasoning.model_copy(
        update={
            "reasoning_statements": (
                reasoning.reasoning_statements[0].model_copy(update={"text": "x causes y."}),
                *reasoning.reasoning_statements[1:],
            )
        }
    )

    valid = service.call_tool(
        "evaluate_reasoning",
        {
            "benchmark_case": case.model_dump(mode="json"),
            "reasoning_artifact": reasoning.model_dump(mode="json"),
        },
    )
    adversarial = service.call_tool(
        "evaluate_reasoning",
        {
            "benchmark_case": case.model_dump(mode="json"),
            "reasoning_artifact": flawed.model_dump(mode="json"),
        },
    )

    assert valid["artifact"]["artifact_type"] == "reasoning_evaluation"
    assert "causal_restraint" in adversarial["evaluation"]["data"]["failed_expectations"]
