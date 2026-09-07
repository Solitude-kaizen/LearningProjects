import pytest

from src.solitude_kaizen.terminal_text import preview_text
from src.solitude_kaizen.conversation_cli import run_talk_to_companion
from src.solitude_kaizen.memory_lens_cli import run_memory_lens


@pytest.mark.parametrize("raw,expected", [
    ("Hello 世界\nKumusta", "Hello 世界\nKumusta"),
    ("\x1b[2J", "\\u001b[2J"),
    ("one\rtwo", "one\\u000dtwo"),
    ("\u202ehidden", "\\u202ehidden"),
    ("\ud800", "\\ud800"),
    ("\u200b", "\\u200b"),
    ("\t", "\\u0009"),
    ("C:\\folder", "C:\\\\folder"),
    ("\u2028", "\\u2028"),
])
def test_preview_exposes_controls_without_hiding_unicode(raw, expected):
    assert preview_text(raw) == expected


def test_reviewed_chat_displays_controls_but_sends_original_text():
    raw = "Question\x1b[2J\u202e C:\\folder"
    memories = [{"text": "Saved\x1b[2J", "category": "personal", "importance": 3, "created_at": "unknown"}]
    output = []
    answers = iter([raw, "yes"])
    requests = []
    def respond(system, message):
        requests.append((system, message))
        assert message == raw
        assert "Saved\x1b[2J" in system
        assert preview_text(system) in output
        assert preview_text(message) in output
        assert all("\x1b" not in line and "\u202e" not in line for line in output)
        return "Answer"
    result = run_talk_to_companion(
        [], memories, review_before_send=True,
        input_function=lambda prompt: next(answers),
        print_function=lambda *parts: output.append(" ".join(map(str, parts))),
        response_function=respond, provider_used_function=lambda: "test",
        provider_info_function=lambda: {"provider": "test", "model": "fake"},
    )
    assert result["status"] == "completed"
    assert len(requests) == 1


def test_lens_does_not_emit_control_sequences_from_memory():
    memories = [{"text": "Python\x1b[2J", "category": "personal", "importance": 3, "created_at": "unknown"}]
    output = []
    run_memory_lens(memories, lambda prompt: "python", lambda *parts: output.append(" ".join(map(str, parts))))
    assert "\x1b" not in "\n".join(output)
    assert "\\u001b" in "\n".join(output)
    assert memories[0]["text"] == "Python\x1b[2J"
