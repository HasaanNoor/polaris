from polaris.literature import build_literature_context
from polaris.projects import LiteratureProjectConfig, ResearchStage, run_research_project
from polaris.reporting.service import generate_report
from polaris.synthesis.models import SynthesisMode, SynthesisRequest
from polaris.synthesis.service import synthesize_assessment
from tests.projects.helpers import single_manifest_project


def test_synthesis_keeps_literature_separate(reporting_pipeline, literature_corpus):
    context = build_literature_context(
        evidence_artifact=reporting_pipeline["evidence"],
        corpus=literature_corpus,
        research_question=reporting_pipeline["research_question"],
    )
    synthesis = synthesize_assessment(
        request=SynthesisRequest(
            coordinated_assessment=reporting_pipeline["coordinated"],
            evidence_artifact=reporting_pipeline["evidence"],
            literature_context=context,
            mode=SynthesisMode.DETERMINISTIC,
        )
    )
    assert "Literature context" in synthesis.overall_summary
    assert synthesis.referenced_claim_ids == reporting_pipeline["synthesis"].referenced_claim_ids


def test_report_renders_literature_section(report_request, literature_corpus):
    context = build_literature_context(
        evidence_artifact=report_request.evidence_artifact,
        corpus=literature_corpus,
        research_question=report_request.research_question,
    )
    generated = generate_report(
        request=report_request.model_copy(update={"literature_context": context})
    )
    assert "## Literature Context" in generated.rendered_content
    assert any(
        entry.reference_kind.value == "literature" for entry in generated.report.reference_index
    )


def test_project_stage_is_optional(tmp_path):
    request = single_manifest_project(tmp_path)
    result = run_research_project(request)
    assert ResearchStage.RETRIEVE_LITERATURE not in result.execution_plan.stages
    assert result.literature_context is None


def test_project_runs_literature_stage_when_configured(tmp_path, literature_dir):
    request = single_manifest_project(tmp_path).model_copy(
        update={
            "literature": LiteratureProjectConfig(
                corpus_path=literature_dir,
                manifest_path=literature_dir / "manifest.json",
                top_k=2,
            )
        }
    )
    result = run_research_project(request)
    assert ResearchStage.RETRIEVE_LITERATURE in result.execution_plan.stages
    assert result.literature_context is not None
    assert result.research_report is not None
    assert "## Literature Context" in result.research_report.rendered_content
