from copy import deepcopy

import pytest

from src.solitude_kaizen import session_notes
from src.solitude_kaizen.memory import ensure_json_file, load_memories
from src.solitude_kaizen.session_note_cli import (
    run_prepare_session_note,
    run_review_session_note,
)


@pytest.fixture
def note_store(tmp_path, monkeypatch):
    def unexpected_network(*args, **kwargs):
        pytest.fail("Session-note editing and review must stay offline.")

    monkeypatch.setattr("socket.socket.connect", unexpected_network)
    path = tmp_path / "memories.json"
    data = {"memories": [], "unrelated": "keep me"}
    ensure_json_file(path, data)
    return path, data


def record_output():
    lines = []
    return lines, lambda *parts: lines.append(" ".join(map(str, parts)))


def scripted_input(answers):
    answers = iter(answers)

    def read(prompt):
        answer = next(answers)
        if answer in (EOFError, KeyboardInterrupt):
            raise answer()
        return answer

    return read


def save_existing(path, data):
    return session_notes.save_session_note(
        path, data,
        {"topic": "Earlier topic", "decisions": "Keep it small",
         "open_questions": "", "next_step": "Try one example"},
        confirmed=True,
    )


def test_prepare_preview_uses_latest_user_text_without_inventing_decisions(note_store):
    path, data = note_store
    original = deepcopy(data)
    original_bytes = path.read_bytes()
    history = [
        {"role": "user", "content": "An earlier question"},
        {"role": "assistant", "content": "An earlier answer"},
        {"role": "user", "content": "Plan a small project"},
        {"role": "assistant", "content": "You have definitely approved spending money"},
    ]
    unchanged_history = deepcopy(history)
    lines, output = record_output()
    answers = iter(["", "", "", "", "yes"])

    def confirm(prompt):
        assert data == original
        assert path.read_bytes() == original_bytes
        if "Type 'yes'" in prompt:
            assert any("Session note preview" in line for line in lines)
            assert any("Decisions: Not recorded" in line for line in lines)
            assert not any("approved spending" in line for line in lines)
        return next(answers)

    result = run_prepare_session_note(path, data, history, confirm, output)
    assert result["status"] == "saved"
    assert result["note"]["topic"] == "Plan a small project"
    assert result["note"]["decisions"] == ""
    assert data["memories"] == []
    assert data["unrelated"] == "keep me"
    assert history == unchanged_history
    assert load_memories(path) == data


def test_manual_note_can_be_revised_after_preview_and_replaces_only_on_yes(note_store):
    path, data = note_store
    save_existing(path, data)
    lines, output = record_output()
    result = run_review_session_note(
        path, data,
        scripted_input([
            "edit", "Bagong paksa", "/clear", "Still unsure", "", "edit",
            "Final topic", "", "", "Check one thing", " YES ",
        ]),
        output,
    )
    assert result["status"] == "saved"
    assert result["note"]["topic"] == "Final topic"
    assert result["note"]["decisions"] == ""
    assert result["note"]["open_questions"] == "Still unsure"
    assert result["note"]["next_step"] == "Check one thing"
    assert load_memories(path) == data
    assert sum("Session note preview" in line for line in lines) == 2
    assert any("replace the one existing" in line for line in lines)


@pytest.mark.parametrize("stage", range(5))
@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt])
def test_interrupted_edit_preserves_saved_bytes_at_every_prompt(
    note_store, stage, interruption,
):
    path, data = note_store
    save_existing(path, data)
    original = deepcopy(data)
    original_bytes = path.read_bytes()
    result = run_review_session_note(
        path, data,
        scripted_input(["edit"] + ["Changed"] * stage + [interruption]),
        lambda *parts: None,
    )
    assert result["status"] == "cancelled"
    assert data == original
    assert path.read_bytes() == original_bytes


@pytest.mark.parametrize("answers", [
    ["/cancel"], ["Topic", "/cancel"], ["Topic", "", "", "", "no"],
    ["Topic", "", "", "", "yes please"],
])
def test_cancelled_preparation_does_not_save(note_store, answers):
    path, data = note_store
    original = deepcopy(data)
    original_bytes = path.read_bytes()
    result = run_prepare_session_note(
        path, data, [], scripted_input(answers), lambda *parts: None,
    )
    assert result["status"] == "cancelled"
    assert data == original
    assert path.read_bytes() == original_bytes


def test_empty_note_is_not_saved(note_store):
    path, data = note_store
    original_bytes = path.read_bytes()
    result = run_prepare_session_note(
        path, data, [], scripted_input(["", "", "", ""]), lambda *parts: None,
    )
    assert result["status"] == "invalid"
    assert "session_note" not in data
    assert path.read_bytes() == original_bytes


def test_oversized_edit_reprompts_without_silently_truncating(note_store):
    path, data = note_store
    lines, output = record_output()
    result = run_prepare_session_note(
        path, data, [],
        scripted_input(["x" * 601, "A shorter topic", "", "", "", "yes"]), output,
    )
    assert result["status"] == "saved"
    assert result["note"]["topic"] == "A shorter topic"
    assert any("too long" in line for line in lines)


@pytest.mark.parametrize("action", ["resume", "forget"])
@pytest.mark.parametrize("confirmation", ["no", "", "y", EOFError, KeyboardInterrupt])
def test_cancelled_review_actions_preserve_state(note_store, action, confirmation):
    path, data = note_store
    save_existing(path, data)
    original = deepcopy(data)
    original_bytes = path.read_bytes()
    result = run_review_session_note(
        path, data, scripted_input([action, confirmation]), lambda *parts: None,
    )
    assert result["status"] == "cancelled"
    assert data == original
    assert path.read_bytes() == original_bytes


def test_resume_warns_of_cloud_context_before_confirmation_without_saving(note_store):
    path, data = note_store
    note = save_existing(path, data)
    original_bytes = path.read_bytes()
    lines, output = record_output()

    def read(prompt):
        if "Type 'yes'" in prompt:
            assert any("cloud provider receives" in line for line in lines)
            return "yes"
        return "resume"

    result = run_review_session_note(path, data, read, output)
    assert result == {"status": "resumed", "note": note}
    result["note"]["topic"] = "Edited separately"
    assert data["session_note"] == note
    assert path.read_bytes() == original_bytes


@pytest.mark.parametrize("action,status", [("dismiss", "dismissed"), ("forget", "forgotten")])
def test_dismiss_and_forget_disclose_retained_chat_details(note_store, action, status):
    path, data = note_store
    note = save_existing(path, data)
    lines, output = record_output()
    result = run_review_session_note(path, data, scripted_input([action, "yes"]), output)
    assert result["status"] == status
    assert any("existing chat that may retain" in line for line in lines)
    if action == "dismiss":
        assert load_memories(path)["session_note"] == note
    else:
        assert "session_note" not in load_memories(path)
        assert any("Earlier backups" in line for line in lines)


def test_invalid_stored_note_does_not_prompt_or_overwrite(note_store):
    path, data = note_store
    data["session_note"] = {"version": 999}
    original = deepcopy(data)
    original_bytes = path.read_bytes()

    def unexpected_input(prompt):
        pytest.fail("Malformed stored notes require separate recovery, not overwriting.")

    assert run_review_session_note(path, data, unexpected_input, lambda *parts: None)[
        "status"
    ] == "invalid"
    assert run_prepare_session_note(path, data, [], unexpected_input, lambda *parts: None)[
        "status"
    ] == "invalid"
    assert data == original
    assert path.read_bytes() == original_bytes


def test_failed_save_reports_failure_without_mutating_live_data(note_store, monkeypatch):
    path, data = note_store
    save_existing(path, data)
    original = deepcopy(data)
    original_bytes = path.read_bytes()

    def fail_replace(*args):
        raise OSError("Test replacement failure")

    monkeypatch.setattr(session_notes.os, "replace", fail_replace)
    result = run_prepare_session_note(
        path, data, [], scripted_input(["New topic", "", "", "", "yes"]),
        lambda *parts: None,
    )
    assert result["status"] == "failed"
    assert data == original
    assert path.read_bytes() == original_bytes
