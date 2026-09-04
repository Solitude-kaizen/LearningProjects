from datetime import datetime
from functools import partial
import runpy

import pytest

from src.solitude_kaizen import conversation_cli
from src.solitude_kaizen.continuous_learning import (
    run_companion_startup,
    run_controlled_learning_cycle,
)
from src.solitude_kaizen.database import (
    add_research_item,
    initialize_database,
)
from src.solitude_kaizen.learning import (
    create_next_learning_lesson,
    read_learning_progress,
)


def test_cycle_is_disabled_when_all_automatic_parts_are_off(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "solitude_kaizen.db"
    monkeypatch.delenv(
        "SK_CONTINUOUS_LEARNING_ENABLED",
        raising=False,
    )
    lesson_called = {"value": False}

    def disabled_component(database_path, current_time=None):
        return {
            "status": "disabled",
            "run": None,
        }

    def unexpected_lesson(database_path, current_time=None):
        lesson_called["value"] = True
        return {
            "status": "created",
            "lesson": {},
        }

    result = run_controlled_learning_cycle(
        database_path,
        current_time=datetime(2026, 9, 2, 9, 0, 0),
        research_function=disabled_component,
        kaizen_function=disabled_component,
        lesson_function=unexpected_lesson,
    )

    assert result["status"] == "disabled"
    assert result["lesson"]["status"] == "disabled"
    assert lesson_called["value"] is False


def test_enabled_cycle_runs_sources_before_offline_lesson(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "solitude_kaizen.db"
    monkeypatch.setenv(
        "SK_CONTINUOUS_LEARNING_ENABLED",
        "true",
    )
    call_order = []

    def research(database_path, current_time=None):
        call_order.append("research")
        return {
            "status": "completed",
            "run": {"new_item_count": 1},
        }

    def kaizen(database_path, current_time=None):
        call_order.append("kaizen")
        return {
            "status": "disabled",
            "discovery": None,
        }

    def lesson(database_path, current_time=None):
        call_order.append("lesson")
        return {
            "status": "created",
            "lesson": {"id": 1},
        }

    result = run_controlled_learning_cycle(
        database_path,
        current_time=datetime(2026, 9, 2, 9, 0, 0),
        research_function=research,
        kaizen_function=kaizen,
        lesson_function=lesson,
    )

    assert call_order == ["research", "kaizen", "lesson"]
    assert result["status"] == "lesson_created"
    assert result["lesson"]["lesson"]["id"] == 1


def test_continuous_learning_does_not_enable_network_sources(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "solitude_kaizen.db"
    monkeypatch.setenv(
        "SK_CONTINUOUS_LEARNING_ENABLED",
        "true",
    )
    monkeypatch.delenv("SK_RESEARCH_ENABLED", raising=False)
    monkeypatch.delenv("KAIZEN_DISCOVERY_ENABLED", raising=False)

    result = run_controlled_learning_cycle(
        database_path,
        current_time=datetime(2026, 9, 2, 9, 0, 0),
    )

    assert result["research"]["status"] == "disabled"
    assert result["kaizen"]["status"] == "disabled"
    assert result["lesson"]["status"] == "no_research"
    assert result["status"] == "waiting_for_research"


def test_cycle_surfaces_partial_research_as_attention(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "solitude_kaizen.db"
    monkeypatch.setenv(
        "SK_CONTINUOUS_LEARNING_ENABLED",
        "true",
    )

    result = run_controlled_learning_cycle(
        database_path,
        current_time=datetime(2026, 9, 2, 9, 0, 0),
        research_function=lambda path, current_time=None: {
            "status": "partial",
            "run": {"new_item_count": 1},
        },
        kaizen_function=lambda path, current_time=None: {
            "status": "disabled",
            "discovery": None,
        },
        lesson_function=lambda path, current_time=None: {
            "status": "created",
            "lesson": {"id": 1},
        },
    )

    assert result["status"] == "attention"


def store_test_research(database_path):
    initialize_database(database_path)
    add_research_item(
        database_path,
        "github",
        "optional-guide-test",
        "Local assistant memory",
        "https://example.com/research",
        "A source that still needs human review.",
        "2026-09-04T08:00:00Z",
        "2026-09-04T09:00:00+08:00",
    )


@pytest.mark.parametrize("existing_lesson", [False, True])
def test_companion_startup_never_creates_or_requires_a_lesson(
    tmp_path,
    monkeypatch,
    existing_lesson,
):
    database_path = tmp_path / "solitude_kaizen.db"
    store_test_research(database_path)

    if existing_lesson:
        create_next_learning_lesson(database_path)

    original_progress = read_learning_progress(database_path)
    monkeypatch.setenv("SK_CONTINUOUS_LEARNING_ENABLED", "true")
    monkeypatch.setenv("SK_RESEARCH_ENABLED", "false")
    monkeypatch.setenv("KAIZEN_DISCOVERY_ENABLED", "false")

    def unexpected_lesson(*args, **kwargs):
        pytest.fail("Normal companion startup must not prepare lessons.")

    monkeypatch.setattr(
        "src.solitude_kaizen.continuous_learning."
        "create_daily_learning_lesson_if_due",
        unexpected_lesson,
    )

    result = run_companion_startup(database_path)

    assert result["status"] == "disabled"
    assert "lesson" not in result
    assert read_learning_progress(database_path) == original_progress


def test_companion_startup_reports_research_without_a_study_gate(tmp_path):
    call_order = []
    current_time = datetime(2026, 9, 4, 9, 0, 0)

    def research(database_path, current_time=None):
        call_order.append(("research", current_time))
        return {"status": "completed", "run": {"new_item_count": 1}}

    def kaizen(database_path, current_time=None):
        call_order.append(("kaizen", current_time))
        return {"status": "disabled", "discovery": None}

    result = run_companion_startup(
        tmp_path / "solitude_kaizen.db",
        current_time=current_time,
        research_function=research,
        kaizen_function=kaizen,
    )

    assert result["status"] == "updated"
    assert call_order == [("research", current_time), ("kaizen", current_time)]
    assert result["ran_at"] == "2026-09-04T09:00:00"
    assert "lesson" not in result


def test_main_can_chat_and_view_research_with_an_unfinished_lesson(
    tmp_path,
    monkeypatch,
    capsys,
):
    database_path = (
        tmp_path / "src" / "solitude_kaizen" / "data" / "solitude_kaizen.db"
    )
    store_test_research(database_path)
    create_next_learning_lesson(database_path)
    original_database = database_path.read_bytes()

    monkeypatch.setenv("SK_CONTINUOUS_LEARNING_ENABLED", "true")
    monkeypatch.setenv("SK_RESEARCH_ENABLED", "false")
    monkeypatch.setenv("KAIZEN_DISCOVERY_ENABLED", "false")
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.last_provider_used", None
    )
    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_groq_response",
        lambda system_prompt, user_message: "Chat works without homework.",
    )

    def unexpected_cycle(*args, **kwargs):
        pytest.fail("The main application must not run the legacy study cycle.")

    monkeypatch.setattr(
        "src.solitude_kaizen.continuous_learning.run_controlled_learning_cycle",
        unexpected_cycle,
    )
    answers = iter(["12", "Hello", "18", "27"])

    def read_input(prompt):
        return next(answers)

    monkeypatch.setattr("builtins.input", read_input)
    monkeypatch.setattr(
        conversation_cli,
        "run_talk_to_companion",
        partial(
            conversation_cli.run_talk_to_companion,
            input_function=read_input,
        ),
    )
    monkeypatch.chdir(tmp_path)

    runpy.run_module("src.solitude_kaizen.main", run_name="__main__")

    output = capsys.readouterr().out
    assert "Chat works without homework." in output
    assert "Title: Local assistant memory" in output
    assert "Optional Learning Guide (not required for chat or research)" in output
    assert "baby-step" not in output
    assert "Reflection question:" not in output
    assert database_path.read_bytes() == original_database
