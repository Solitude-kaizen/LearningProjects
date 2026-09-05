import copy
import json
from datetime import datetime

import pytest

from src.solitude_kaizen import session_notes
from src.solitude_kaizen.session_notes import (
    MAX_FIELD_CHARS,
    NOTE_FIELDS,
    draft_session_note,
    forget_session_note,
    format_session_note,
    get_session_note,
    save_session_note,
    validate_session_note_fields,
)


def make_draft(**changes):
    draft = {
        "topic": "Review a fictional training plan",
        "decisions": "Use two sessions",
        "open_questions": "Which room is available?",
        "next_step": "Ask about the room",
    }
    return {**draft, **changes}


def make_note(**changes):
    return {
        **make_draft(),
        "version": 1,
        "saved_at": "2026-09-06T10:00:00+00:00",
        **changes,
    }


@pytest.fixture
def memory_file(tmp_path):
    path = tmp_path / "memories.json"
    data = {
        "memories": [{"text": "Fictional test memory"}],
        "unrelated": {"keep": [1, 2, 3]},
    }
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    return path, data


def test_draft_copies_only_latest_user_message_and_preserves_history():
    history = [
        {"role": "user", "content": "An earlier subject"},
        {"role": "assistant", "content": "We decided to spend money."},
        {"role": "user", "content": "  Compare two training outlines  "},
        {"role": "assistant", "content": "Your next step is to buy tools."},
    ]
    before = copy.deepcopy(history)

    draft = draft_session_note(history)

    assert draft == {
        "topic": "Compare two training outlines",
        "decisions": "",
        "open_questions": "",
        "next_step": "",
    }
    assert history == before


@pytest.mark.parametrize("history", [[], [{"role": "assistant", "content": "Hi"}]])
def test_draft_without_user_message_is_blank(history):
    assert draft_session_note(history) == dict.fromkeys(NOTE_FIELDS, "")


@pytest.mark.parametrize("content", ["", "  ", None, 12])
def test_latest_empty_or_invalid_user_message_does_not_reuse_earlier_topic(content):
    history = [
        {"role": "user", "content": "Old subject"},
        {"role": "user", "content": content},
    ]
    assert draft_session_note(history) == dict.fromkeys(NOTE_FIELDS, "")


def test_long_draft_is_bounded_and_marks_truncation():
    draft = draft_session_note([
        {"role": "user", "content": "x" * (MAX_FIELD_CHARS + 1)},
    ])
    assert len(draft["topic"]) == MAX_FIELD_CHARS
    assert draft["topic"].endswith(" [truncated]")
    assert not draft["decisions"]


def test_exact_limit_is_not_truncated():
    content = "x" * MAX_FIELD_CHARS
    assert draft_session_note([{"role": "user", "content": content}])["topic"] == content


def test_field_validation_returns_trimmed_independent_fields():
    draft = make_draft(topic="  Training  ", next_step="  ", extra="discard")
    before = draft.copy()
    validated = validate_session_note_fields(draft)
    assert validated == {**make_draft(), "topic": "Training", "next_step": ""}
    assert draft == before
    assert validated is not draft


@pytest.mark.parametrize("field", NOTE_FIELDS)
def test_field_validation_rejects_missing_non_text_and_oversized(field):
    missing = make_draft()
    del missing[field]
    for invalid in (missing, make_draft(**{field: 5}), make_draft(**{field: "x" * 601})):
        with pytest.raises(ValueError):
            validate_session_note_fields(invalid)
    assert len(validate_session_note_fields(make_draft(**{field: "x" * 600}))[field]) == 600


@pytest.mark.parametrize("draft", [None, [], {}, dict.fromkeys(NOTE_FIELDS, " \n ")])
def test_field_validation_rejects_invalid_or_empty_note(draft):
    with pytest.raises(ValueError):
        validate_session_note_fields(draft)


def test_legacy_memory_data_has_no_note_and_is_unchanged():
    data = {"memories": []}
    assert get_session_note(data) is None
    assert data == {"memories": []}


def test_get_returns_independent_validated_record():
    stored = make_note(topic="  Fictional plan  ")
    data = {"memories": [], "session_note": stored}
    note = get_session_note(data)
    assert note["topic"] == "Fictional plan"
    assert note["version"] == 1
    assert note["saved_at"] == stored["saved_at"]
    note["decisions"] = "Different"
    assert data["session_note"] is stored
    assert stored == make_note(topic="  Fictional plan  ")


@pytest.mark.parametrize("stored", [
    None,
    [],
    {},
    make_note(version=True),
    make_note(version="1"),
    make_note(version=2),
    make_note(saved_at=None),
    make_note(saved_at="2026-09-06"),
    make_note(saved_at="2026-99-06T10:00:00"),
    make_note(topic=5),
    make_note(topic="x" * 601),
    make_note(**dict.fromkeys(NOTE_FIELDS, "")),
])
def test_invalid_stored_record_is_not_silently_repaired(stored):
    data = {"memories": [], "session_note": stored}
    before = copy.deepcopy(data)
    with pytest.raises(ValueError):
        get_session_note(data)
    assert data == before


def test_format_displays_labels_and_unrecorded_blanks():
    assert format_session_note(make_draft(decisions="", next_step="")) == (
        "Topic: Review a fictional training plan\n"
        "Decisions: Not recorded\n"
        "Open questions: Which room is available?\n"
        "Possible next step: Not recorded"
    )


@pytest.mark.parametrize("confirmed", [False, None, "yes", 1, [], {}])
def test_save_without_exact_confirmation_does_not_validate_or_write(memory_file, confirmed):
    path, data = memory_file
    before = path.read_bytes()
    assert save_session_note(path, data, None, confirmed=confirmed) is None
    assert path.read_bytes() == before
    assert "session_note" not in data
    assert list(path.parent.iterdir()) == [path]


def test_save_default_is_cancelled(memory_file):
    path, data = memory_file
    assert save_session_note(path, data, make_draft()) is None
    assert "session_note" not in data


def test_save_and_replace_preserve_unrelated_data_and_memory_list_identity(memory_file):
    path, data = memory_file
    memories = data["memories"]
    unrelated = data["unrelated"]
    original = copy.deepcopy(data)

    saved = save_session_note(path, data, make_draft(topic="  First  "), confirmed=True)

    assert saved == get_session_note(data)
    assert saved["topic"] == "First"
    assert datetime.fromisoformat(saved["saved_at"]).tzinfo is not None
    assert json.loads(path.read_text(encoding="utf-8")) == data
    assert data["memories"] is memories
    assert data["unrelated"] is unrelated
    assert {key: data[key] for key in original} == original
    saved["topic"] = "Do not mutate stored data"
    assert data["session_note"]["topic"] == "First"

    replacement = save_session_note(path, data, make_draft(topic="Second"), confirmed=True)
    assert data["session_note"]["topic"] == replacement["topic"] == "Second"
    assert data["memories"] is memories
    assert json.loads(path.read_text(encoding="utf-8")) == data
    assert list(path.parent.iterdir()) == [path]


def test_invalid_draft_leaves_existing_disk_and_note_unchanged(memory_file):
    path, data = memory_file
    save_session_note(path, data, make_draft(), confirmed=True)
    stored = data["session_note"]
    before = path.read_bytes()
    with pytest.raises(ValueError):
        save_session_note(path, data, dict.fromkeys(NOTE_FIELDS, ""), confirmed=True)
    assert path.read_bytes() == before
    assert data["session_note"] is stored


@pytest.mark.parametrize("operation", ["save", "forget"])
def test_invalid_existing_note_cannot_be_replaced_or_deleted(memory_file, operation):
    path, data = memory_file
    data["session_note"] = {"version": 99}
    path.write_text(json.dumps(data), encoding="utf-8")
    before = path.read_bytes()
    snapshot = copy.deepcopy(data)
    with pytest.raises(ValueError):
        if operation == "save":
            save_session_note(path, data, make_draft(), confirmed=True)
        else:
            forget_session_note(path, data, confirmed=True)
    assert path.read_bytes() == before
    assert data == snapshot
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize("confirmed", [False, None, "yes", 1])
def test_forget_cancelled_does_not_write(memory_file, confirmed):
    path, data = memory_file
    save_session_note(path, data, make_draft(), confirmed=True)
    before = path.read_bytes()
    stored = data["session_note"]
    assert forget_session_note(path, data, confirmed=confirmed) is None
    assert path.read_bytes() == before
    assert data["session_note"] is stored


def test_forget_default_is_cancelled(memory_file):
    path, data = memory_file
    save_session_note(path, data, make_draft(), confirmed=True)
    before = path.read_bytes()
    assert forget_session_note(path, data) is None
    assert path.read_bytes() == before


def test_forget_absent_note_does_not_write(memory_file):
    path, data = memory_file
    before = path.read_bytes()
    assert forget_session_note(path, data, confirmed=True) is None
    assert path.read_bytes() == before
    assert data == json.loads(before)


def test_forget_removes_only_note(memory_file):
    path, data = memory_file
    original = copy.deepcopy(data)
    memories = data["memories"]
    unrelated = data["unrelated"]
    saved = save_session_note(path, data, make_draft(), confirmed=True)

    removed = forget_session_note(path, data, confirmed=True)

    assert removed == saved
    assert data == original
    assert data["memories"] is memories
    assert data["unrelated"] is unrelated
    assert json.loads(path.read_text(encoding="utf-8")) == original
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize("operation", ["save", "forget"])
@pytest.mark.parametrize("failure", ["dump", "fsync", "replace"])
def test_failed_persistence_preserves_disk_and_in_memory_state(
    memory_file, monkeypatch, operation, failure,
):
    path, data = memory_file
    save_session_note(path, data, make_draft(), confirmed=True)
    before = path.read_bytes()
    snapshot = copy.deepcopy(data)
    memories = data["memories"]
    stored = data["session_note"]

    def fail(*args, **kwargs):
        raise OSError("Simulated persistence failure")

    target = session_notes.json if failure == "dump" else session_notes.os
    monkeypatch.setattr(target, failure, fail)
    with pytest.raises(OSError, match="Simulated persistence failure"):
        if operation == "save":
            save_session_note(path, data, make_draft(topic="Replacement"), confirmed=True)
        else:
            forget_session_note(path, data, confirmed=True)

    assert path.read_bytes() == before
    assert data == snapshot
    assert data["memories"] is memories
    assert data["session_note"] is stored
    assert list(path.parent.iterdir()) == [path]


def test_atomic_replace_uses_complete_same_directory_temporary_file(memory_file, monkeypatch):
    path, data = memory_file
    before = path.read_bytes()
    replace = session_notes.os.replace
    observed = []

    def inspect_replace(source, destination):
        assert source.parent == path.parent
        assert source != path
        assert destination == path
        assert path.read_bytes() == before
        assert "session_note" not in data
        assert json.loads(source.read_text(encoding="utf-8"))["session_note"]["topic"] == "New"
        observed.append(source)
        replace(source, destination)

    monkeypatch.setattr(session_notes.os, "replace", inspect_replace)
    save_session_note(path, data, make_draft(topic="New"), confirmed=True)
    assert len(observed) == 1
    assert not observed[0].exists()


def test_serialization_error_cleans_temporary_file_without_changing_disk(memory_file):
    path, data = memory_file
    before = path.read_bytes()
    data["unrelated"]["not_json"] = {1, 2}
    with pytest.raises(TypeError):
        save_session_note(path, data, make_draft(), confirmed=True)
    assert "session_note" not in data
    assert path.read_bytes() == before
    assert list(path.parent.iterdir()) == [path]
