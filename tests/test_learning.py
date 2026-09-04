from datetime import datetime

import pytest

from src.solitude_kaizen.database import (
    add_research_item,
    initialize_database,
)
from src.solitude_kaizen.learning import (
    LEARNING_PURPOSE,
    build_learning_lesson,
    create_daily_learning_lesson_if_due,
    create_next_learning_lesson,
    finish_active_learning_lesson,
    read_learning_progress,
    score_research_item,
    select_research_item,
)


def make_research_item(
    item_id=1,
    source="github",
    title="Local assistant memory",
    summary="A public project about safe memory.",
):
    return {
        "id": item_id,
        "source": source,
        "external_id": str(item_id),
        "title": title,
        "url": f"https://example.com/item/{item_id}",
        "summary": summary,
        "published_at": "2026-09-01T09:00:00Z",
        "discovered_at": "2026-09-02T09:00:00+08:00",
    }


def store_research_item(database_path, item):
    add_research_item(
        database_path,
        item["source"],
        item["external_id"],
        item["title"],
        item["url"],
        item["summary"],
        item["published_at"],
        item["discovered_at"],
    )


def test_learning_purpose_describes_optional_study_not_model_training():
    assert "optional study activities" in LEARNING_PURPOSE
    assert "safely" in LEARNING_PURPOSE
    assert "does not train SK's model" in LEARNING_PURPOSE


def test_learning_brain_prefers_relevant_research():
    generic_paper = make_research_item(
        item_id=1,
        source="arxiv",
        title="A general computing paper",
        summary="A public computing abstract.",
    )
    memory_project = make_research_item(
        item_id=2,
        source="github",
        title="Private memory for a local assistant",
    )

    selected = select_research_item(
        [generic_paper, memory_project]
    )

    assert selected["id"] == 2
    assert score_research_item(memory_project) > (
        score_research_item(generic_paper)
    )


def test_lesson_marks_public_metadata_as_unreviewed():
    lesson = build_learning_lesson(make_research_item())

    assert lesson["topic"] == "Local assistant memory"
    assert lesson["evidence_summary"].startswith(
        "Unreviewed public metadata:"
    )
    assert "10 minutes" in lesson["baby_step"]
    assert "before changing any code" in (
        lesson["improvement_proposal"]
    )


def test_create_lesson_reports_when_research_is_empty(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"

    result = create_next_learning_lesson(database_path)

    assert result == {
        "status": "no_research",
        "lesson": None,
    }


def test_create_lesson_stores_one_active_baby_step(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)
    store_research_item(database_path, make_research_item())

    result = create_next_learning_lesson(
        database_path,
        current_time=datetime(2026, 9, 2, 10, 0, 0),
    )
    second_result = create_next_learning_lesson(database_path)

    assert result["status"] == "created"
    assert result["lesson"]["status"] == "ready"
    assert result["lesson"]["evidence_status"] == "unreviewed"
    assert result["lesson"]["proposal_status"] == "pending"
    assert second_result["status"] == "existing"
    assert second_result["lesson"]["id"] == result["lesson"]["id"]


def test_finish_lesson_requires_a_reflection(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)
    store_research_item(database_path, make_research_item())
    create_next_learning_lesson(database_path)

    with pytest.raises(ValueError, match="reflection is required"):
        finish_active_learning_lesson(database_path, "   ")


def test_finish_lesson_stores_reflection_but_not_approval(
    tmp_path,
):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)
    store_research_item(database_path, make_research_item())
    create_next_learning_lesson(database_path)

    result = finish_active_learning_lesson(
        database_path,
        "Memory needs limits; the source still needs testing.",
        current_time=datetime(2026, 9, 2, 10, 15, 0),
    )

    assert result["status"] == "completed"
    assert result["lesson"]["status"] == "completed"
    assert result["lesson"]["evidence_status"] == "reviewed"
    assert result["lesson"]["proposal_status"] == "pending"
    assert result["lesson"]["user_reflection"] == (
        "Memory needs limits; the source still needs testing."
    )


def test_next_lesson_uses_new_research_after_completion(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)
    first_item = make_research_item(item_id=1)
    second_item = make_research_item(
        item_id=2,
        title="Evaluation for AI assistants",
    )
    store_research_item(database_path, first_item)
    store_research_item(database_path, second_item)

    first_result = create_next_learning_lesson(database_path)
    finish_active_learning_lesson(
        database_path,
        "I reviewed the first source and recorded uncertainty.",
    )
    second_result = create_next_learning_lesson(database_path)
    progress = read_learning_progress(database_path)

    assert second_result["status"] == "created"
    assert second_result["lesson"]["research_item_id"] != (
        first_result["lesson"]["research_item_id"]
    )
    assert progress == {
        "total": 2,
        "ready": 1,
        "completed": 1,
        "pending_proposals": 1,
    }


def test_automatic_lesson_is_limited_to_one_per_day(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)
    store_research_item(database_path, make_research_item(item_id=1))
    store_research_item(database_path, make_research_item(item_id=2))
    first_time = datetime(2026, 9, 2, 9, 0, 0)

    first_result = create_daily_learning_lesson_if_due(
        database_path,
        current_time=first_time,
    )
    finish_active_learning_lesson(
        database_path,
        "I reviewed the source and kept its uncertainty visible.",
        current_time=datetime(2026, 9, 2, 9, 15, 0),
    )
    same_day_result = create_daily_learning_lesson_if_due(
        database_path,
        current_time=datetime(2026, 9, 2, 18, 0, 0),
    )
    next_day_result = create_daily_learning_lesson_if_due(
        database_path,
        current_time=datetime(2026, 9, 3, 9, 0, 0),
    )

    assert first_result["status"] == "created"
    assert same_day_result["status"] == "skipped_daily_limit"
    assert same_day_result["lesson"]["id"] == (
        first_result["lesson"]["id"]
    )
    assert next_day_result["status"] == "created"
    assert next_day_result["lesson"]["id"] != (
        first_result["lesson"]["id"]
    )
