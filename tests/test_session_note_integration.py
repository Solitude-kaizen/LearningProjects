"""Temporary-data checks for explicit session-note consent and continuity."""

from copy import deepcopy
from datetime import datetime
from functools import partial
import json
import runpy
import zipfile

import pytest

from src.solitude_kaizen import conversation_cli
from src.solitude_kaizen.continuity import (
    ARCHIVE_MEMORIES_PATH,
    create_continuity_bundle,
    preview_continuity_restore,
    restore_continuity_bundle,
    verify_continuity_bundle,
)
from src.solitude_kaizen.database import initialize_database
from src.solitude_kaizen.memory import ensure_json_file, load_memories


def sample_note(topic="Private session topic marker"):
    return {
        "version": 1,
        "saved_at": "2026-09-06T12:00:00+08:00",
        "topic": topic,
        "decisions": "Private decision marker",
        "open_questions": "Private open question marker",
        "next_step": "Private next step marker",
    }


def create_workspace(tmp_path, note=None):
    data_directory = tmp_path / "src" / "solitude_kaizen" / "data"
    paths = {
        "memory": data_directory / "memories.json",
        "profile": data_directory / "profile.json",
        "database": data_directory / "solitude_kaizen.db",
        "identity": tmp_path / "SK_IDENTITY.md",
        "backups": data_directory / "backups",
    }
    data = {
        "memories": [{
            "text": "Ordinary saved memory",
            "category": "test",
            "importance": 3,
            "created_at": "2026-09-06T11:00:00",
        }],
        "unrelated_metadata": {"keep": True},
    }
    if note is not None:
        data["session_note"] = deepcopy(note)
    ensure_json_file(paths["memory"], data)
    ensure_json_file(paths["profile"], {"user_name": "Test User"})
    initialize_database(paths["database"])
    paths["identity"].write_text(
        "# Solitude-Kaizen Identity\n\nIdentity version: 1\n",
        encoding="utf-8",
    )
    return paths, data


@pytest.fixture
def run_sk(tmp_path, monkeypatch):
    """Run only against a temporary workspace and a deterministic fake model."""
    for setting in (
        "SK_RESEARCH_ENABLED",
        "KAIZEN_DISCOVERY_ENABLED",
        "SK_CONTINUOUS_LEARNING_ENABLED",
    ):
        monkeypatch.setenv(setting, "false")

    def unexpected_network(*args, **kwargs):
        pytest.fail("Session-note integration tests must not contact a network.")

    monkeypatch.setattr("requests.sessions.Session.request", unexpected_network)
    monkeypatch.setattr("socket.create_connection", unexpected_network)
    monkeypatch.chdir(tmp_path)
    original_talk = conversation_cli.run_talk_to_companion

    def run(answers):
        remaining_answers = iter(answers)
        requests = []

        def read_input(prompt):
            try:
                answer = next(remaining_answers)
            except StopIteration:
                pytest.fail(f"Unexpected additional input request: {prompt}")
            if answer in (EOFError, KeyboardInterrupt):
                raise answer()
            return answer

        def fake_response(system_prompt, user_message):
            requests.append((system_prompt, user_message))
            return "A synthetic reply with no session-note content."

        monkeypatch.setattr("builtins.input", read_input)
        monkeypatch.setattr(
            conversation_cli,
            "run_talk_to_companion",
            partial(
                original_talk,
                input_function=read_input,
                response_function=fake_response,
                provider_used_function=lambda: "test",
            ),
        )
        state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
        assert list(remaining_answers) == [], "The scripted workflow ended early."
        return state, requests

    return run


def test_saved_note_survives_restart_without_startup_disclosure_or_attachment(
    tmp_path, run_sk, capsys,
):
    paths, original = create_workspace(tmp_path)
    state, requests = run_sk([
        "12", "Draft topic marker", "28",
        "", "Approved decision marker", "Approved question marker",
        "Approved next step marker", "yes", "27",
    ])
    saved = load_memories(paths["memory"])
    note = saved["session_note"]
    assert "Draft topic marker" in note["topic"]
    assert note["decisions"] == "Approved decision marker"
    assert note["open_questions"] == "Approved question marker"
    assert note["next_step"] == "Approved next step marker"
    assert saved["memories"] == original["memories"]
    assert saved["unrelated_metadata"] == original["unrelated_metadata"]
    assert state["active_session_note"] is None
    assert len(requests) == 1  # Saving a note does not ask a model for a summary.
    capsys.readouterr()

    restarted, requests = run_sk(["12", "Hello again", "27"])
    output = capsys.readouterr().out
    assert restarted["active_session_note"] is None
    assert len(requests) == 1
    for field in ("topic", "decisions", "open_questions", "next_step"):
        assert note[field] not in output
        assert note[field] not in requests[0][0]
    assert load_memories(paths["memory"])["session_note"] == note


def test_explicit_resume_adds_note_to_chat_without_changing_saved_data(
    tmp_path, run_sk,
):
    note = sample_note()
    paths, original = create_workspace(tmp_path, note)
    original_bytes = paths["memory"].read_bytes()
    state, requests = run_sk([
        "29", "resume", "yes", "12", "Continue please", "27",
    ])
    assert len(requests) == 1
    for field in ("topic", "decisions", "open_questions", "next_step"):
        assert note[field] in requests[0][0]
    assert state["active_session_note"] == note
    assert len(state["conversation_history"]) == 2
    assert load_memories(paths["memory"]) == original
    assert paths["memory"].read_bytes() == original_bytes


@pytest.mark.parametrize("confirmation", ["no", "", EOFError, KeyboardInterrupt])
def test_cancelled_resume_never_activates_saved_note(
    tmp_path, run_sk, confirmation,
):
    note = sample_note()
    paths, original = create_workspace(tmp_path, note)
    original_bytes = paths["memory"].read_bytes()
    state, requests = run_sk([
        "29", "resume", confirmation, "12", "An unrelated question", "27",
    ])
    assert state["active_session_note"] is None
    assert note["topic"] not in requests[0][0]
    assert load_memories(paths["memory"]) == original
    assert paths["memory"].read_bytes() == original_bytes


@pytest.mark.parametrize("confirmation", ["no", EOFError, KeyboardInterrupt])
def test_cancelled_note_edit_preserves_active_context_and_saved_bytes(
    tmp_path, run_sk, confirmation,
):
    note = sample_note()
    paths, original = create_workspace(tmp_path, note)
    original_bytes = paths["memory"].read_bytes()
    state, requests = run_sk([
        "29", "resume", "yes", "28",
        "Unsaved replacement topic", "Unsaved decision", "Unsaved question",
        "Unsaved step", confirmation, "12", "Continue please", "27",
    ])
    assert state["active_session_note"] == note
    assert note["topic"] in requests[0][0]
    assert "Unsaved replacement topic" not in requests[0][0]
    assert load_memories(paths["memory"]) == original
    assert paths["memory"].read_bytes() == original_bytes


@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt, "/cancel"])
def test_interrupted_note_field_preserves_saved_and_active_note(
    tmp_path, run_sk, interruption,
):
    note = sample_note()
    paths, original = create_workspace(tmp_path, note)
    original_bytes = paths["memory"].read_bytes()
    state, requests = run_sk([
        "29", "resume", "yes", "28", interruption, "27",
    ])
    assert state["active_session_note"] == note
    assert requests == []
    assert load_memories(paths["memory"]) == original
    assert paths["memory"].read_bytes() == original_bytes


@pytest.mark.parametrize("confirmation", ["yes", "no", EOFError, KeyboardInterrupt])
def test_clear_conversation_handles_active_note_with_empty_chat_history(
    tmp_path, run_sk, confirmation,
):
    note = sample_note()
    paths, original = create_workspace(tmp_path, note)
    state, requests = run_sk([
        "29", "resume", "yes", "14", confirmation,
        "12", "Hello after clear decision", "27",
    ])
    assert len(requests) == 1
    if confirmation == "yes":
        assert state["active_session_note"] is None
        assert note["topic"] not in requests[0][0]
    else:
        assert state["active_session_note"] == note
        assert note["topic"] in requests[0][0]
    assert len(state["conversation_history"]) == 2
    assert load_memories(paths["memory"]) == original


def test_forgetting_normal_memory_preserves_saved_session_note(tmp_path, run_sk):
    note = sample_note()
    paths, original = create_workspace(tmp_path, note)
    state, requests = run_sk(["6", "1", "yes", "27"])
    saved = load_memories(paths["memory"])
    assert saved["memories"] == []
    assert state["memories"] == []
    assert saved["session_note"] == note
    assert saved["unrelated_metadata"] == original["unrelated_metadata"]
    assert requests == []


def test_confirmed_saved_note_edit_requires_fresh_resume_for_chat(tmp_path, run_sk):
    note = sample_note()
    paths, original = create_workspace(tmp_path, note)
    state, requests = run_sk([
        "29", "resume", "yes", "29", "edit",
        "", "Revised approved decision", "/clear", "", "yes",
        "12", "A new question", "27",
    ])
    saved = load_memories(paths["memory"])
    revised = saved["session_note"]
    assert revised["topic"] == note["topic"]
    assert revised["decisions"] == "Revised approved decision"
    assert revised["open_questions"] == ""
    assert revised["next_step"] == note["next_step"]
    assert saved["memories"] == original["memories"]
    assert state["active_session_note"] is None
    assert len(requests) == 1
    assert note["topic"] not in requests[0][0]
    assert revised["decisions"] not in requests[0][0]


@pytest.mark.parametrize("action", ["dismiss", "forget"])
def test_dismiss_or_forget_detaches_note_and_preserves_normal_memories(
    tmp_path, run_sk, action,
):
    note = sample_note()
    paths, original = create_workspace(tmp_path, note)
    answers = ["29", "resume", "yes", "29", action]
    if action == "forget":
        answers.append("yes")
    answers.extend(["12", "Next question", "27"])
    state, requests = run_sk(answers)
    saved = load_memories(paths["memory"])
    assert state["active_session_note"] is None
    assert note["topic"] not in requests[0][0]
    assert saved["memories"] == original["memories"]
    assert saved["unrelated_metadata"] == original["unrelated_metadata"]
    if action == "forget":
        assert "session_note" not in saved
    else:
        assert saved["session_note"] == note


@pytest.mark.parametrize("original_note", [None, sample_note("Original note")])
def test_continuity_roundtrip_restores_note_or_legacy_note_free_state(
    tmp_path, original_note,
):
    paths, original = create_workspace(tmp_path, original_note)
    original_bytes = paths["memory"].read_bytes()
    created = create_continuity_bundle(
        paths["backups"], paths["database"], paths["profile"],
        paths["memory"], paths["identity"],
        current_time=datetime(2026, 9, 6, 12, 0, 0),
    )
    assert created["verification"]["status"] == "valid"
    assert created["verification"]["file_count"] == 4
    with zipfile.ZipFile(created["bundle_path"]) as bundle:
        assert json.loads(bundle.read(ARCHIVE_MEMORIES_PATH)) == original

    replacement = deepcopy(original)
    replacement["session_note"] = sample_note("Newer note to protect")
    paths["memory"].write_text(
        json.dumps(replacement, indent=4), encoding="utf-8",
    )
    preview = preview_continuity_restore(
        created["bundle_path"], paths["database"], paths["profile"],
        paths["memory"], paths["identity"],
    )
    assert preview["status"] == "ready"
    assert preview["change_count"] == 1
    restored = restore_continuity_bundle(
        created["bundle_path"], paths["backups"], paths["database"],
        paths["profile"], paths["memory"], paths["identity"],
        confirmation=preview["confirmation_phrase"],
        current_time=datetime(2026, 9, 6, 12, 1, 0),
    )
    assert restored["status"] == "restored"
    assert paths["memory"].read_bytes() == original_bytes
    assert load_memories(paths["memory"]) == original
    emergency = restored["emergency_bundle_path"]
    assert verify_continuity_bundle(emergency)["status"] == "valid"
    with zipfile.ZipFile(emergency) as bundle:
        assert json.loads(bundle.read(ARCHIVE_MEMORIES_PATH)) == replacement
