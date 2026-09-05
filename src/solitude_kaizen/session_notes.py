"""Optional, user-reviewed continuity notes with local-only persistence."""

from datetime import datetime, timezone

from .json_storage import write_json_atomic


NOTE_FIELDS = ("topic", "decisions", "open_questions", "next_step")
MAX_FIELD_CHARS = 600

_FIELD_LABELS = {
    "topic": "Topic",
    "decisions": "Decisions",
    "open_questions": "Open questions",
    "next_step": "Possible next step",
}
_TRUNCATION_MARKER = " [truncated]"


def draft_session_note(history):
    """Copy only the latest user message as a topic for explicit review.

    Decisions, questions, and next steps are intentionally left for the user
    to record. Assistant replies never become accepted facts automatically.
    """
    draft = dict.fromkeys(NOTE_FIELDS, "")
    for message in reversed(history):
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            topic = content.strip()
            if len(topic) > MAX_FIELD_CHARS:
                topic = (
                    topic[:MAX_FIELD_CHARS - len(_TRUNCATION_MARKER)]
                    + _TRUNCATION_MARKER
                )
            draft["topic"] = topic
        break
    return draft


def validate_session_note_fields(draft):
    """Return a trimmed copy of the four bounded, user-editable fields."""
    if not isinstance(draft, dict):
        raise ValueError("The session note must contain the four text fields.")

    fields = {}
    for field in NOTE_FIELDS:
        value = draft.get(field)
        if not isinstance(value, str):
            raise ValueError(f"{_FIELD_LABELS[field]} must be text.")
        value = value.strip()
        if len(value) > MAX_FIELD_CHARS:
            raise ValueError(
                f"{_FIELD_LABELS[field]} must be at most "
                f"{MAX_FIELD_CHARS} characters."
            )
        fields[field] = value

    if not any(fields.values()):
        raise ValueError("Record at least one session-note field before saving.")
    return fields


def get_session_note(memory_data):
    """Read a validated independent note, without repairing stored data."""
    if not isinstance(memory_data, dict):
        raise ValueError("Memory data must be an object.")
    if "session_note" not in memory_data:
        return None

    stored = memory_data["session_note"]
    if not isinstance(stored, dict):
        raise ValueError("The stored session note is invalid.")
    if type(stored.get("version")) is not int or stored["version"] != 1:
        raise ValueError("The stored session-note version is unsupported.")
    fields = validate_session_note_fields(stored)
    saved_at = stored.get("saved_at")
    if not isinstance(saved_at, str) or "T" not in saved_at:
        raise ValueError("The stored session-note timestamp is invalid.")
    try:
        datetime.fromisoformat(saved_at)
    except ValueError as error:
        raise ValueError("The stored session-note timestamp is invalid.") from error

    return {**fields, "version": 1, "saved_at": saved_at}


def format_session_note(note):
    """Display a draft or stored note without implying blanks are decisions."""
    return "\n".join(
        f"{_FIELD_LABELS[field]}: {note[field] or 'Not recorded'}"
        for field in NOTE_FIELDS
    )


def save_session_note(memory_path, memory_data, draft, confirmed=False):
    """Save one reviewed note only after an explicit boolean confirmation."""
    if confirmed is not True:
        return None
    get_session_note(memory_data)
    fields = validate_session_note_fields(draft)
    saved = {
        **fields,
        "version": 1,
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    updated_data = {**memory_data, "session_note": saved}
    write_json_atomic(memory_path, updated_data)
    memory_data["session_note"] = saved.copy()
    return saved


def forget_session_note(memory_path, memory_data, confirmed=False):
    """Delete only the reviewed note, preserving memories and unrelated data."""
    if confirmed is not True:
        return None
    note = get_session_note(memory_data)
    if note is None:
        return None
    updated_data = memory_data.copy()
    del updated_data["session_note"]
    write_json_atomic(memory_path, updated_data)
    del memory_data["session_note"]
    return note
