"""Optional, local-only editing and explicit activation of a session note."""

from .session_notes import (
    MAX_FIELD_CHARS,
    NOTE_FIELDS,
    draft_session_note,
    forget_session_note,
    format_session_note,
    get_session_note,
    save_session_note,
    validate_session_note_fields,
)


FIELD_LABELS = {
    "topic": "Topic / latest user message",
    "decisions": "Decisions you approved",
    "open_questions": "Unresolved questions",
    "next_step": "Possible next step",
}


def _cancel(print_function):
    print_function("Cancelled. The saved note and active context were not changed.")
    return {"status": "cancelled", "note": None}


def _display_note(note, print_function):
    if note.get("saved_at"):
        print_function("Saved at:", note["saved_at"])
    print_function(format_session_note(note))


def _edit_and_save(memory_path, memory_data, draft, input_function, print_function):
    draft = {field: draft[field] for field in NOTE_FIELDS}
    print_function("Local draft only: no AI call and no automatic fact checking.")
    print_function("Blank keeps a field; /clear empties it; /cancel cancels.")
    print_function(f"Each field may contain up to {MAX_FIELD_CHARS} characters.")
    print_function("Do not include passwords, API keys, or other credentials.")
    if "session_note" in memory_data:
        print_function("Saving will replace the one existing session note.")
        print_function("--- Existing saved note ---")
        _display_note(get_session_note(memory_data), print_function)

    try:
        while True:
            print_function("--- Draft (not saved) ---")
            _display_note(draft, print_function)
            for field in NOTE_FIELDS:
                while True:
                    value = input_function(FIELD_LABELS[field] + ": ")
                    stripped = value.strip()
                    if stripped.casefold() == "/cancel":
                        return _cancel(print_function)
                    if len(stripped) > MAX_FIELD_CHARS:
                        print_function("That field is too long; shorten it or /cancel.")
                        continue
                    if stripped.casefold() == "/clear":
                        draft[field] = ""
                    elif stripped:
                        draft[field] = stripped
                    break

            try:
                draft = validate_session_note_fields(draft)
            except ValueError as error:
                print_function("Nothing saved:", str(error))
                return {"status": "invalid", "note": None}

            print_function("--- Session note preview ---")
            _display_note(draft, print_function)
            print_function(
                "Stored locally in memories.json, separate from automatic memory "
                "selection. Future continuity backups include it and are unencrypted."
            )
            confirmation = input_function(
                "Type 'yes' to save, 'edit' to revise, anything else to cancel: "
            ).strip().casefold()
            if confirmation == "edit":
                continue
            if confirmation != "yes":
                return _cancel(print_function)

            note = save_session_note(memory_path, memory_data, draft, confirmed=True)
            print_function("Session note saved. Use option 29 to review and resume it.")
            print_function("It has not been sent to a model or activated for chat.")
            return {"status": "saved", "note": note}
    except (EOFError, KeyboardInterrupt):
        return _cancel(print_function)
    except (OSError, ValueError):
        print_function("Could not save the session note. Existing data was left unchanged.")
        return {"status": "failed", "note": None}


def run_prepare_session_note(
    memory_path,
    memory_data,
    conversation_history,
    input_function=None,
    print_function=None,
):
    """Prepare a user-editable note without saving chat history or calling AI."""
    if input_function is None:
        input_function = input
    if print_function is None:
        print_function = print
    try:
        get_session_note(memory_data)
    except ValueError:
        print_function("The saved session note is invalid. It was left unchanged.")
        return {"status": "invalid", "note": None}

    return _edit_and_save(
        memory_path, memory_data, draft_session_note(conversation_history),
        input_function, print_function,
    )


def run_review_session_note(
    memory_path,
    memory_data,
    input_function=None,
    print_function=None,
):
    """Return an activation decision; the caller owns current-session context."""
    if input_function is None:
        input_function = input
    if print_function is None:
        print_function = print
    try:
        note = get_session_note(memory_data)
    except ValueError:
        print_function("The saved session note is invalid. It was left unchanged.")
        return {"status": "invalid", "note": None}
    if note is None:
        print_function("No session note is saved. Option 28 can prepare one.")
        return {"status": "empty", "note": None}

    print_function("--- Saved session note ---")
    _display_note(note, print_function)
    print_function("Viewing this note does not send it to a model.")
    try:
        action = input_function(
            "Choose 'resume', 'edit', 'forget', or 'dismiss'; anything else cancels: "
        ).strip().casefold()
        if action == "edit":
            return _edit_and_save(
                memory_path, memory_data, note, input_function, print_function,
            )
        if action == "resume":
            print_function(
                "This note will be included in later chats during this session. "
                "A cloud provider receives it if you use cloud chat."
            )
            confirmation = input_function(
                "Type 'yes' to use this note as chat context, anything else to cancel: "
            )
            if confirmation.strip().casefold() != "yes":
                return _cancel(print_function)
            print_function("Session note resumed. Option 12 starts your next chat.")
            return {"status": "resumed", "note": note}
        if action == "forget":
            print_function("Only the saved session note will be deleted, not memories.")
            print_function("Earlier backups and existing chat may still contain its details.")
            confirmation = input_function(
                "Type 'yes' to forget this note, anything else to cancel: "
            )
            if confirmation.strip().casefold() != "yes":
                return _cancel(print_function)
            forget_session_note(memory_path, memory_data, confirmed=True)
            print_function("Session note forgotten and detached from direct chat context.")
            print_function("Use option 14 to clear existing chat that may retain details.")
            return {"status": "forgotten", "note": None}
        if action == "dismiss":
            print_function("Session note detached; the saved copy was kept.")
            print_function("Use option 14 to clear existing chat that may retain details.")
            return {"status": "dismissed", "note": None}
        return _cancel(print_function)
    except (EOFError, KeyboardInterrupt):
        return _cancel(print_function)
    except (OSError, ValueError):
        print_function("Could not change the session note. Existing data was left unchanged.")
        return {"status": "failed", "note": None}
