import pytest
from pydantic import ValidationError

from polaris.schemas.common import QuestionCategory
from polaris.schemas.research_question import ResearchQuestion


def test_valid_research_question_creation(example_data):
    question = ResearchQuestion.model_validate(example_data["research_question"])

    assert question.question_id == "rq_education_life_expectancy"
    assert question.category == QuestionCategory.CORRELATIONAL


def test_research_question_json_round_trip(example_data):
    question = ResearchQuestion.model_validate(example_data["research_question"])
    serialized = question.model_dump_json()

    assert ResearchQuestion.model_validate_json(serialized) == question


def test_research_question_rejects_unknown_fields(example_data, copy_data):
    data = copy_data(example_data["research_question"])
    data["unexpected"] = "not allowed"

    with pytest.raises(ValidationError):
        ResearchQuestion.model_validate(data)


def test_research_question_rejects_invalid_temporal_range(example_data, copy_data):
    data = copy_data(example_data["research_question"])
    data["temporal_scope"]["start"] = 2020
    data["temporal_scope"]["end"] = 2010

    with pytest.raises(ValidationError):
        ResearchQuestion.model_validate(data)


def test_descriptive_question_does_not_require_exposure(example_data, copy_data):
    data = copy_data(example_data["research_question"])
    data["category"] = "descriptive"
    data["raw_text"] = "What was the trend in life expectancy from 2010 to 2020?"
    data["exposure_variables"] = []

    question = ResearchQuestion.model_validate(data)

    assert question.category == QuestionCategory.DESCRIPTIVE
    assert question.exposure_variables == []


def test_research_question_requires_identifier(example_data, copy_data):
    data = copy_data(example_data["research_question"])
    del data["question_id"]

    with pytest.raises(ValidationError):
        ResearchQuestion.model_validate(data)
