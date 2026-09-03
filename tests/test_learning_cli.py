from src.solitude_kaizen.database import (
    add_research_item,
    initialize_database,
)
from src.solitude_kaizen.learning import (
    get_active_learning_lesson,
    list_pending_learning_proposals,
    read_proposal_review_history,
)
from src.solitude_kaizen.learning_cli import (
    run_complete_current_learning_lesson,
    run_review_pending_learning_proposal,
    run_start_or_view_learning_lesson,
    run_view_learning_progress,
    run_view_proposal_review_history,
)


def create_output_recorder():
    messages = []

    def record_output(*values):
        messages.append(" ".join(str(value) for value in values))

    return messages, record_output


def create_learning_database(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)
    add_research_item(
        database_path,
        "github",
        "learning-cli-1",
        "Bounded memory for a local assistant",
        "https://example.com/bounded-memory",
        "A public project about bounded assistant memory.",
        "2026-09-03T08:00:00Z",
        "2026-09-03T09:00:00+08:00",
    )

    return database_path


def complete_learning_lesson(database_path):
    run_start_or_view_learning_lesson(
        database_path,
        print_function=lambda *values: None,
    )

    return run_complete_current_learning_lesson(
        database_path,
        input_function=lambda prompt: (
            "The idea is useful, but its limits need testing."
        ),
        print_function=lambda *values: None,
    )


def test_start_lesson_flow_explains_when_research_is_empty(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    messages, record_output = create_output_recorder()

    result = run_start_or_view_learning_lesson(
        database_path,
        print_function=record_output,
    )

    assert result["status"] == "no_research"
    assert "SK needs research before creating a lesson." in messages


def test_start_lesson_flow_creates_and_displays_one_lesson(tmp_path):
    database_path = create_learning_database(tmp_path)
    messages, record_output = create_output_recorder()

    result = run_start_or_view_learning_lesson(
        database_path,
        print_function=record_output,
    )

    assert result["status"] == "created"
    assert "SK prepared one new baby-step lesson." in messages
    assert "Evidence status: unreviewed" in messages
    assert get_active_learning_lesson(database_path)["id"] == (
        result["lesson"]["id"]
    )


def test_complete_lesson_flow_stores_reflection_for_human_review(
    tmp_path,
):
    database_path = create_learning_database(tmp_path)
    run_start_or_view_learning_lesson(
        database_path,
        print_function=lambda *values: None,
    )
    messages, record_output = create_output_recorder()

    result = run_complete_current_learning_lesson(
        database_path,
        input_function=lambda prompt: (
            "I understand the idea, but the evidence needs review."
        ),
        print_function=record_output,
    )

    assert result["status"] == "completed"
    assert result["lesson"]["proposal_status"] == "pending"
    assert len(list_pending_learning_proposals(database_path)) == 1
    assert (
        "The improvement proposal still requires human review."
        in messages
    )


def test_proposal_review_flow_approves_planning_without_execution(
    tmp_path,
):
    database_path = create_learning_database(tmp_path)
    complete_learning_lesson(database_path)
    proposal = list_pending_learning_proposals(database_path)[0]
    answers = iter(
        [
            str(proposal["id"]),
            "approve",
            "Prepare a separate tested implementation plan.",
        ]
    )
    messages, record_output = create_output_recorder()

    result = run_review_pending_learning_proposal(
        database_path,
        input_function=lambda prompt: next(answers),
        print_function=record_output,
    )
    progress = run_view_learning_progress(
        database_path,
        print_function=record_output,
    )
    history = run_view_proposal_review_history(
        database_path,
        print_function=record_output,
    )

    assert result["status"] == "recorded"
    assert result["proposal_status"] == "approved"
    assert progress["pending_proposals"] == 0
    assert history == read_proposal_review_history(database_path)
    assert history[0]["reason"] == (
        "Prepare a separate tested implementation plan."
    )
    assert (
        "Approved for separate planning. No code was changed."
        in messages
    )


def test_proposal_review_flow_stops_after_invalid_id(tmp_path):
    database_path = create_learning_database(tmp_path)
    complete_learning_lesson(database_path)
    answers = iter(["not-a-number"])
    messages, record_output = create_output_recorder()

    result = run_review_pending_learning_proposal(
        database_path,
        input_function=lambda prompt: next(answers),
        print_function=record_output,
    )

    assert result["status"] == "invalid_proposal_id"
    assert "Please enter a valid proposal ID." in messages
    assert read_proposal_review_history(database_path) == []
