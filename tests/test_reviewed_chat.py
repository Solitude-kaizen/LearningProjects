from copy import deepcopy
from functools import partial
import runpy

import pytest

from src.solitude_kaizen.ai_service import ProviderError
from src.solitude_kaizen.conversation_cli import run_talk_to_companion
from src.solitude_kaizen import conversation_cli, memory
from src.solitude_kaizen.database import initialize_database


def provider_info():
    return {"provider": "test", "model": "fake", "type": "cloud"}


def sample_context():
    return (
        [{"role": "user", "content": "Earlier question"}, {"role": "assistant", "content": "Earlier answer"}],
        [{"text": "Practice Python", "category": "learning", "importance": 3, "created_at": "unknown"}],
        {"topic": "Our plan", "decisions": "Try a small example", "open_questions": "", "next_step": "Test"},
    )


@pytest.mark.parametrize("confirmation", ["", "no", "/cancel", EOFError, KeyboardInterrupt])
def test_preview_cancellation_keeps_all_context(monkeypatch, confirmation):
    history, memories, note = sample_context()
    original = deepcopy((history, memories, note))
    output = []
    answers = iter(["Python question", confirmation])
    def read(prompt):
        answer = next(answers)
        if "yes" in prompt:
            assert "--- Review Before Send ---" in output
            assert (history, memories, note) == original
        if answer in (EOFError, KeyboardInterrupt):
            raise answer()
        return answer
    def forbidden(*args):
        pytest.fail("Canceled preview must not contact inference or look up a used provider.")
    monkeypatch.setattr("builtins.input", read)
    result = run_talk_to_companion(
        history, memories, session_note=note, review_before_send=True,
        print_function=lambda *parts: output.append(" ".join(map(str, parts))),
        response_function=forbidden, provider_used_function=forbidden,
        provider_info_function=provider_info,
    )
    assert result["status"] == "cancelled"
    assert (history, memories, note) == original
    assert any("Practice Python" in line and "Earlier answer" in line and "Our plan" in line for line in output)


@pytest.mark.parametrize("confirmation", ["yes", " YES "])
def test_preview_sends_exact_displayed_text_once(confirmation):
    history, memories, note = sample_context()
    output = []
    answers = iter(["  Python question\nwith formatting  ", confirmation])
    calls = []
    def respond(system, message):
        assert system == output[output.index("Application system prompt:") + 1]
        assert message == output[output.index("Your message:") + 1]
        calls.append((system, message))
        return "Answer"
    result = run_talk_to_companion(
        history, memories, session_note=note, review_before_send=True,
        input_function=lambda prompt: next(answers),
        print_function=lambda *parts: output.append(" ".join(map(str, parts))),
        response_function=respond, provider_used_function=lambda: "test",
        provider_info_function=provider_info,
    )
    assert result["status"] == "completed"
    assert len(calls) == 1
    assert len(history) == 4
    assert history[-1]["content"] == "Answer"


def test_invalid_provider_does_not_append_a_turn():
    history, memories, note = sample_context()
    original = deepcopy(history)
    def fail():
        raise ProviderError("config", "invalid_provider", "Invalid configuration")
    result = run_talk_to_companion(
        history, memories, review_before_send=True,
        input_function=lambda prompt: "Python", print_function=lambda *args: None,
        provider_info_function=fail,
        response_function=lambda *args: pytest.fail("No request allowed"),
    )
    assert result["status"] == "failed"
    assert history == original


def test_normal_chat_has_no_preview_or_extra_prompt():
    history, memories, note = sample_context()
    prompts = []
    def read(prompt):
        prompts.append(prompt)
        return "Python"
    result = run_talk_to_companion(
        history, memories, input_function=read, print_function=lambda *args: None,
        response_function=lambda *args: "Answer", provider_used_function=lambda: "test",
        provider_info_function=lambda: pytest.fail("Normal chat does not need preview metadata"),
    )
    assert result["status"] == "completed"
    assert prompts == ["You: "]


@pytest.mark.parametrize("confirmation", ["yes", "no", KeyboardInterrupt])
def test_main_reviewed_chat_preserves_files_and_obeys_confirmation(tmp_path, monkeypatch, capsys, confirmation):
    directory = tmp_path / "src" / "solitude_kaizen" / "data"
    paths = [directory / "memories.json", directory / "profile.json", directory / "solitude_kaizen.db"]
    data = {"memories": sample_context()[1]}
    memory.ensure_json_file(paths[0], data)
    memory.ensure_json_file(paths[1], {"user_name": "Test User"})
    initialize_database(paths[2])
    originals = {path: path.read_bytes() for path in paths}
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    calls = []
    def respond(system, message):
        calls.append((system, message))
        return "Answer"
    def forbidden(*args, **kwargs):
        pytest.fail("Integration test must not contact network.")
    monkeypatch.setattr("socket.socket.connect", forbidden)
    monkeypatch.setattr(conversation_cli, "run_talk_to_companion", partial(
        run_talk_to_companion, response_function=respond,
        provider_info_function=provider_info, provider_used_function=lambda: "test",
    ))
    answers = iter(["32", "Python question", confirmation, "27"])
    def read(prompt):
        answer = next(answers)
        if answer is KeyboardInterrupt:
            raise KeyboardInterrupt()
        return answer
    monkeypatch.setattr("builtins.input", read)
    monkeypatch.chdir(tmp_path)
    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    output = capsys.readouterr().out
    assert "--- Review Before Send ---" in output
    assert "Goodbye!" in output
    assert len(calls) == (1 if confirmation == "yes" else 0)
    assert len(state["conversation_history"]) == (2 if confirmation == "yes" else 0)
    assert all(path.read_bytes() == before for path, before in originals.items())


@pytest.mark.parametrize("response", [None, "", " \n\t", 0, False, {"unexpected": "private raw data"}, ["unexpected"]])
@pytest.mark.parametrize("reviewed", [False, True])
def test_invalid_provider_output_never_becomes_conversation(response, reviewed):
    history, memories, note = sample_context()
    original = deepcopy((history, memories, note))
    answers = iter(["Python", "yes"])
    output = []
    result = run_talk_to_companion(
        history, memories, session_note=note, review_before_send=reviewed,
        input_function=lambda prompt: next(answers),
        print_function=lambda *parts: output.append(" ".join(map(str, parts))),
        response_function=lambda *args: response,
        provider_info_function=provider_info,
        provider_used_function=lambda: pytest.fail("Invalid output is not a successful reply"),
    )
    assert result["status"] == "invalid_response"
    assert (history, memories, note) == original
    assert "private raw data" not in "\n".join(output)
    assert any("no usable text" in line for line in output)


def test_reviewed_context_has_only_six_recent_messages_and_five_memories():
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"TURN_{i:02d}"} for i in range(20)]
    memories = [dict(sample_context()[1][0], text=f"Python MEMORY_{i:02d}") for i in range(8)]
    answers = iter(["Python", "yes"])
    output = []
    def respond(system, message):
        for i in range(20):
            assert (f"TURN_{i:02d}" in system) == (i >= 14)
        for i in range(8):
            assert (f"MEMORY_{i:02d}" in system) == (i < 5)
        assert system in output
        return "Answer"
    run_talk_to_companion(
        history, memories, review_before_send=True,
        input_function=lambda prompt: next(answers),
        print_function=lambda *parts: output.append(" ".join(map(str, parts))),
        response_function=respond, provider_info_function=provider_info,
        provider_used_function=lambda: "test",
    )
    assert len(history) == 20


@pytest.mark.parametrize("failure", [KeyboardInterrupt, "provider_error", "unavailable"])
def test_confirmed_review_failure_keeps_previous_context(failure):
    from src.solitude_kaizen.ai_service import AI_UNAVAILABLE_MESSAGE
    history, memories, note = sample_context()
    original = deepcopy((history, memories, note))
    answers = iter(["Python", "yes"])
    calls = []
    def respond(*args):
        calls.append(args)
        if failure is KeyboardInterrupt:
            raise KeyboardInterrupt()
        if failure == "provider_error":
            raise ProviderError("test", "connection", "Unavailable")
        return AI_UNAVAILABLE_MESSAGE
    result = run_talk_to_companion(
        history, memories, session_note=note, review_before_send=True,
        input_function=lambda prompt: next(answers), print_function=lambda *args: None,
        response_function=respond, provider_info_function=provider_info,
        provider_used_function=lambda: pytest.fail("Failed request has no successful provider"),
    )
    assert result["status"] in ("interrupted", "failed")
    assert len(calls) == 1
    assert (history, memories, note) == original
