from datetime import datetime

import pytest

from src.solitude_kaizen.database import (
    add_research_item,
    initialize_database,
)
from src.solitude_kaizen.learning import (
    create_next_learning_lesson,
    finish_active_learning_lesson,
    list_pending_learning_proposals,
    read_proposal_review_history,
    review_learning_proposal,
)


def create_completed_proposal(database_path):
    initialize_database(database_path)
    add_research_item(
        database_path,
        "github",
        "proposal-test-1",
        "Bounded memory for a local assistant",
        "https://example.com/bounded-memory",
        "A public project about bounded assistant memory.",
        "2026-09-02T08:00:00Z",
        "2026-09-02T09:00:00+08:00",
    )
    created = create_next_learning_lesson(database_path)
    finish_active_learning_lesson(
        database_path,
        "The idea may help, but its limits still need testing.",
    )

    return created["lesson"]["id"]


def test_only_completed_lessons_are_ready_for_proposal_review(
    tmp_path,
):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)
    add_research_item(
        database_path,
        "github",
        "proposal-test-1",
        "Bounded memory for a local assistant",
        "https://example.com/bounded-memory",
        "A public project about bounded assistant memory.",
        "2026-09-02T08:00:00Z",
        "2026-09-02T09:00:00+08:00",
    )
    create_next_learning_lesson(database_path)

    assert list_pending_learning_proposals(database_path) == []

    finish_active_learning_lesson(
        database_path,
        "The source was reviewed, but the claim needs testing.",
    )

    assert len(list_pending_learning_proposals(database_path)) == 1


def test_unfinished_lesson_cannot_be_approved(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)
    add_research_item(
        database_path,
        "github",
        "proposal-test-1",
        "Bounded memory for a local assistant",
        "https://example.com/bounded-memory",
        "A public project about bounded assistant memory.",
        "2026-09-02T08:00:00Z",
        "2026-09-02T09:00:00+08:00",
    )
    created = create_next_learning_lesson(database_path)

    result = review_learning_proposal(
        database_path,
        created["lesson"]["id"],
        "approve",
        "Attempted before completing the lesson.",
    )

    assert result["status"] == "lesson_incomplete"
    assert read_proposal_review_history(database_path) == []


def test_approve_records_reason_without_executing_proposal(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    lesson_id = create_completed_proposal(database_path)

    result = review_learning_proposal(
        database_path,
        lesson_id,
        "approve",
        "The idea is ready for a separate implementation plan.",
        current_time=datetime(2026, 9, 2, 11, 0, 0),
    )
    history = read_proposal_review_history(database_path)

    assert result["status"] == "recorded"
    assert result["proposal_status"] == "approved"
    assert list_pending_learning_proposals(database_path) == []
    assert history[0]["action"] == "approved"
    assert history[0]["reason"] == (
        "The idea is ready for a separate implementation plan."
    )


def test_reject_closes_proposal_and_records_reason(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    lesson_id = create_completed_proposal(database_path)

    result = review_learning_proposal(
        database_path,
        lesson_id,
        "reject",
        "The evidence is too weak for SK.",
    )

    assert result["status"] == "recorded"
    assert result["proposal_status"] == "rejected"
    assert read_proposal_review_history(database_path)[0][
        "action"
    ] == "rejected"


def test_postpone_keeps_proposal_pending_with_history(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    lesson_id = create_completed_proposal(database_path)

    result = review_learning_proposal(
        database_path,
        lesson_id,
        "postpone",
        "Review this after the memory foundation is stronger.",
    )
    pending = list_pending_learning_proposals(database_path)

    assert result["status"] == "recorded"
    assert result["proposal_status"] == "pending"
    assert len(pending) == 1
    assert pending[0]["latest_review_action"] == "postponed"


def test_review_requires_valid_action_and_reason(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    lesson_id = create_completed_proposal(database_path)

    with pytest.raises(ValueError, match="approve, reject"):
        review_learning_proposal(
            database_path,
            lesson_id,
            "execute",
            "Try it now.",
        )

    with pytest.raises(ValueError, match="reason is required"):
        review_learning_proposal(
            database_path,
            lesson_id,
            "approve",
            "   ",
        )


def test_terminal_proposal_cannot_be_reviewed_twice(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    lesson_id = create_completed_proposal(database_path)
    review_learning_proposal(
        database_path,
        lesson_id,
        "approve",
        "Proceed only through a separate implementation plan.",
    )

    second_result = review_learning_proposal(
        database_path,
        lesson_id,
        "reject",
        "Attempt to change an already final decision.",
    )

    assert second_result["status"] == "already_decided"
    assert second_result["proposal_status"] == "approved"
    assert len(read_proposal_review_history(database_path)) == 1


def test_unknown_proposal_is_reported_without_history(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)

    result = review_learning_proposal(
        database_path,
        999,
        "postpone",
        "The proposal does not exist.",
    )

    assert result["status"] == "not_found"
    assert read_proposal_review_history(database_path) == []
