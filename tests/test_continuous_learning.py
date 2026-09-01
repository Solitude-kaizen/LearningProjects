from datetime import datetime

from src.solitude_kaizen.continuous_learning import (
    run_controlled_learning_cycle,
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
