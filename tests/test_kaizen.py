from datetime import datetime

from src.solitude_kaizen.ai_service import ProviderError
from src.solitude_kaizen.database import (
    get_latest_kaizen_discovery,
)
from src.solitude_kaizen.kaizen import (
    KAIZEN_DISCOVERY_MODEL,
    KAIZEN_PUBLIC_PROJECT_DESCRIPTION,
    generate_daily_discovery,
    maybe_run_daily_kaizen,
    run_daily_kaizen_if_due,
)


def test_daily_kaizen_stores_completed_discovery(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    current_time = datetime(2026, 8, 30, 21, 0, 0)

    result = run_daily_kaizen_if_due(
        database_path,
        current_time=current_time,
        discovery_function=lambda: "Evidence and proposal",
    )

    discovery = get_latest_kaizen_discovery(database_path)

    assert result["status"] == "completed"
    assert discovery["run_date"] == "2026-08-30"
    assert discovery["status"] == "completed"
    assert discovery["report"] == "Evidence and proposal"
    assert discovery["provider"] == "groq"
    assert discovery["error_kind"] is None


def test_daily_kaizen_runs_only_once_per_date(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    current_time = datetime(2026, 8, 30, 21, 0, 0)
    call_count = {"value": 0}

    def fake_discovery():
        call_count["value"] += 1
        return "Daily proposal"

    first_result = run_daily_kaizen_if_due(
        database_path,
        current_time=current_time,
        discovery_function=fake_discovery,
    )
    second_result = run_daily_kaizen_if_due(
        database_path,
        current_time=current_time,
        discovery_function=fake_discovery,
    )

    assert first_result["status"] == "completed"
    assert second_result["status"] == "skipped"
    assert call_count["value"] == 1


def test_daily_kaizen_runs_again_on_next_date(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    call_count = {"value": 0}

    def fake_discovery():
        call_count["value"] += 1
        return "Daily proposal"

    run_daily_kaizen_if_due(
        database_path,
        current_time=datetime(2026, 8, 30, 21, 0, 0),
        discovery_function=fake_discovery,
    )
    result = run_daily_kaizen_if_due(
        database_path,
        current_time=datetime(2026, 8, 31, 8, 0, 0),
        discovery_function=fake_discovery,
    )

    assert result["status"] == "completed"
    assert call_count["value"] == 2


def test_daily_kaizen_records_provider_failure(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"

    def failed_discovery():
        raise ProviderError(
            provider="groq",
            kind="rate_limit",
            message="Groq rate limit reached.",
            retryable=True,
            fallback_allowed=False,
        )

    result = run_daily_kaizen_if_due(
        database_path,
        current_time=datetime(2026, 8, 30, 21, 0, 0),
        discovery_function=failed_discovery,
    )

    assert result["status"] == "failed"
    assert result["discovery"]["error_kind"] == "rate_limit"
    assert result["discovery"]["report"] == (
        "Groq rate limit reached."
    )


def test_daily_kaizen_is_disabled_by_default(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "solitude_kaizen.db"
    monkeypatch.delenv(
        "KAIZEN_DISCOVERY_ENABLED",
        raising=False,
    )

    result = maybe_run_daily_kaizen(database_path)

    assert result["status"] == "disabled"


def test_generate_daily_discovery_uses_public_context(
    monkeypatch,
):
    captured_request = {}

    def fake_groq_response(
        system_prompt,
        user_message,
        model,
    ):
        captured_request["system_prompt"] = system_prompt
        captured_request["user_message"] = user_message
        captured_request["model"] = model
        return "Proposal with sources"

    monkeypatch.setattr(
        "src.solitude_kaizen.kaizen.generate_groq_response",
        fake_groq_response,
    )

    response = generate_daily_discovery()

    assert response == "Proposal with sources"
    assert captured_request["model"] == KAIZEN_DISCOVERY_MODEL
    assert captured_request["user_message"] == (
        KAIZEN_PUBLIC_PROJECT_DESCRIPTION
    )
    assert "private user information" in (
        captured_request["system_prompt"]
    )
