from functools import partial
import json
import runpy

import pytest

from src.solitude_kaizen import source_review_cli
from src.solitude_kaizen.ai_service import AI_UNAVAILABLE_MESSAGE, ProviderError
from src.solitude_kaizen.database import initialize_database
from src.solitude_kaizen.memory import ensure_json_file


def inputs(confirmation="yes"):
    return ["Fictional report", "https://example.org/report", "Four people tried it.",
            "No follow-up was done.", "/done", "Are long-term benefits established?", confirmation]


def model_text():
    return json.dumps({
        "answer": "Long-term benefits are not established in this excerpt.",
        "evidence": [{"quote": "No follow-up was done.", "explanation": "Outcomes were not followed."}],
        "uncertainties": ["Long-term outcomes are absent."],
    })


@pytest.fixture
def run_review(monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("These tests must not contact a provider or fetch a link.")
    monkeypatch.setattr("requests.sessions.Session.request", no_network)

    def run(answers, response=None):
        answers = iter(answers)
        output, requests = [], []

        def read(prompt):
            value = next(answers)
            if value in (EOFError, KeyboardInterrupt):
                raise value()
            return value

        def model(system_prompt, message):
            assert any("Request preview" in line for line in output)
            assert any("may have costs" in line for line in output)
            requests.append((system_prompt, message))
            if isinstance(response, BaseException):
                raise response
            return response if response is not None else model_text()

        result = source_review_cli.run_source_review(
            read, lambda *parts: output.append(" ".join(map(str, parts))), model,
            lambda: {"provider": "test", "model": "fake", "type": "cloud"},
            lambda: "test",
        )
        return result, output, requests

    return run


def test_confirmed_review_sends_only_supplied_material_once(run_review):
    result, output, requests = run_review(inputs())
    assert result["status"] == "completed"
    assert len(requests) == 1
    assert json.loads(requests[0][1]) == {
        "title": "Fictional report", "url": "https://example.org/report",
        "excerpt": "Four people tried it.\nNo follow-up was done.",
        "question": "Are long-term benefits established?",
    }
    assert any("not independent fact verification" in line for line in output)


@pytest.mark.parametrize("stage", range(7))
@pytest.mark.parametrize("interrupt", [EOFError, KeyboardInterrupt, "/cancel"])
def test_pre_request_interruption_at_every_input_never_sends(run_review, stage, interrupt):
    answers = inputs()[:stage] + [interrupt]
    result, output, requests = run_review(answers)
    assert result["status"] == "cancelled"
    assert not requests


@pytest.mark.parametrize("confirmation", ["", "no", "y", "yes please"])
def test_only_exact_confirmation_requests_review(run_review, confirmation):
    result, _, requests = run_review(inputs(confirmation))
    assert result["status"] == "cancelled"
    assert not requests


def test_oversized_excerpt_aborts_before_model(run_review):
    result, _, requests = run_review(["Title", "", "x" * 6001])
    assert result["status"] == "invalid"
    assert not requests


def test_too_many_empty_lines_is_bounded(run_review):
    result, _, requests = run_review(["Title", ""] + [""] * 101)
    assert result["status"] == "invalid"
    assert not requests


@pytest.mark.parametrize("response,status", [
    ("not JSON", "invalid_response"),
    (model_text().replace("No follow-up was done.", "Lasting benefits were proven."), "invalid_response"),
    (AI_UNAVAILABLE_MESSAGE, "failed"),
    (KeyboardInterrupt(), "interrupted"),
    (ProviderError("ollama", "connection", "Test unavailable"), "failed"),
])
def test_failed_review_never_retries_or_presents_unchecked_output(run_review, response, status):
    result, output, requests = run_review(inputs(), response)
    assert result["status"] == status
    assert len(requests) == 1
    assert not any("Model interpretation (check" in line for line in output)
    if status == "interrupted":
        assert any("may already have reached" in line for line in output)


def test_invalid_provider_prevents_request(monkeypatch):
    answers = iter(inputs())
    def invalid_provider():
        raise ProviderError("config", "invalid_provider", "Invalid configuration")
    def no_request(*args):
        pytest.fail("Invalid configuration must not send a review.")
    result = source_review_cli.run_source_review(
        lambda prompt: next(answers), lambda *parts: None, no_request, invalid_provider,
    )
    assert result["status"] == "failed"


def test_main_review_isolated_from_memories_active_note_and_history(tmp_path, monkeypatch):
    directory = tmp_path / "src" / "solitude_kaizen" / "data"
    memory_path = directory / "memories.json"
    profile_path = directory / "profile.json"
    database_path = directory / "solitude_kaizen.db"
    note = {"version": 1, "saved_at": "2026-09-06T12:00:00+08:00", "topic": "PRIVATE_NOTE",
            "decisions": "", "open_questions": "", "next_step": ""}
    data = {"memories": [{"text": "PRIVATE_MEMORY", "category": "test", "importance": 3,
                          "created_at": "unknown"}], "session_note": note}
    ensure_json_file(memory_path, data)
    ensure_json_file(profile_path, {"user_name": "PRIVATE_PROFILE"})
    initialize_database(database_path)
    originals = {path: path.read_bytes() for path in (memory_path, profile_path, database_path)}
    requests = []
    def model(system, message):
        requests.append((system, message))
        return model_text()
    original_review = source_review_cli.run_source_review
    monkeypatch.setattr(source_review_cli, "run_source_review", partial(
        original_review, response_function=model,
        provider_info_function=lambda: {"provider": "test", "model": "fake"},
        provider_used_function=lambda: "test",
    ))
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    def no_network(*args, **kwargs):
        pytest.fail("Main workflow test must remain offline.")
    monkeypatch.setattr("requests.sessions.Session.request", no_network)
    answers = iter(["29", "resume", "yes", "30"] + inputs() + ["27"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.chdir(tmp_path)
    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    assert len(requests) == 1
    assert "PRIVATE" not in " ".join(requests[0])
    assert state["conversation_history"] == []
    assert state["active_session_note"] == note
    assert state["memory_data"] == data
    assert all(path.read_bytes() == original for path, original in originals.items())
