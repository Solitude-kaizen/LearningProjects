from copy import deepcopy
from functools import partial
import runpy

import pytest

from src.solitude_kaizen import conversation_cli, memory
from src.solitude_kaizen.database import initialize_database
from src.solitude_kaizen.memory import ensure_json_file, load_memories

from src.solitude_kaizen.ai_service import ProviderError
from src.solitude_kaizen.conversation_cli import (
    run_clear_conversation,
    run_talk_to_companion,
    run_view_ai_provider,
    run_view_conversation_status,
)


def create_output_recorder():
    messages = []

    def record_output(*values):
        messages.append(" ".join(str(value) for value in values))

    return messages, record_output


def create_memories():
    return [
        {
            "text": "Build SK carefully",
            "category": "project",
            "importance": 5,
            "created_at": "2026-09-03T09:00:00",
        }
    ]


def test_talk_flow_builds_context_and_records_one_complete_turn():
    conversation_history = [
        {"role": "user", "content": "What is Python?"},
        {
            "role": "assistant",
            "content": "Python is a programming language.",
        },
    ]
    captured_request = {}

    def fake_response(system_prompt, user_message):
        captured_request["system_prompt"] = system_prompt
        captured_request["user_message"] = user_message

        return "A function is a reusable block of code."

    messages, record_output = create_output_recorder()

    result = run_talk_to_companion(
        conversation_history,
        create_memories(),
        input_function=lambda prompt: "Explain a function.",
        print_function=record_output,
        response_function=fake_response,
        provider_used_function=lambda: "ollama",
    )

    assert result == {
        "status": "completed",
        "error": None,
        "response": "A function is a reusable block of code.",
        "provider": "ollama",
    }
    assert captured_request["user_message"] == "Explain a function."
    assert "Build SK carefully" in captured_request["system_prompt"]
    assert "User: What is Python?" in (
        captured_request["system_prompt"]
    )
    assert "Explain a function." not in (
        captured_request["system_prompt"]
    )
    assert conversation_history[-2:] == [
        {"role": "user", "content": "Explain a function."},
        {
            "role": "assistant",
            "content": "A function is a reusable block of code.",
        },
    ]
    assert "[Provider: ollama]" in messages


def test_talk_selects_memories_for_each_current_question_without_saving(tmp_path):
    memory_path = tmp_path / "memories.json"
    memory_data = {
        "memories": [
            {
                "text": f"Unrelated reminder {index}",
                "category": "personal",
                "importance": 5,
                "created_at": "2026-09-04T12:00:00",
            }
            for index in range(6)
        ] + [
            {
                "text": "Practice Python loops",
                "category": "learning",
                "importance": 1,
                "created_at": "2026-08-01T09:00:00",
            },
            {
                "text": "Prefer short walks",
                "category": "health",
                "importance": 1,
                "created_at": "2026-08-01T09:00:00",
            },
        ]
    }
    ensure_json_file(memory_path, memory_data)
    memories = load_memories(memory_path)["memories"]
    original = deepcopy(memories)
    original_bytes = memory_path.read_bytes()
    conversation_history = []
    captured_requests = []

    def fake_response(system_prompt, user_message):
        captured_requests.append((system_prompt, user_message))
        return "Test reply."

    for question in ["Help with Python", "Any health suggestions?"]:
        result = run_talk_to_companion(
            conversation_history,
            memories,
            input_function=lambda prompt: question,
            print_function=lambda *parts: None,
            response_function=fake_response,
            provider_used_function=lambda: "ollama",
        )
        assert result["status"] == "completed"

    python_prompt, python_question = captured_requests[0]
    health_prompt, health_question = captured_requests[1]
    assert python_question == "Help with Python"
    assert health_question == "Any health suggestions?"
    assert "Practice Python loops" in python_prompt
    assert "Prefer short walks" not in python_prompt
    assert "Prefer short walks" in health_prompt
    assert "Practice Python loops" not in health_prompt
    assert all("Unrelated reminder" not in prompt for prompt, _ in captured_requests)
    assert len(conversation_history) == 4
    assert memories == original
    assert memory_path.read_bytes() == original_bytes


def test_talk_flow_removes_unanswered_turn_after_provider_error():
    conversation_history = [
        {"role": "user", "content": "Earlier question"},
        {"role": "assistant", "content": "Earlier answer"},
    ]
    original_history = [message.copy() for message in conversation_history]

    def failed_response(system_prompt, user_message):
        raise ProviderError(
            provider="ollama",
            kind="connection",
            message="Could not connect to Ollama.",
            retryable=True,
            fallback_allowed=False,
        )

    def unexpected_provider_lookup():
        pytest.fail("A failed response has no successful provider.")

    messages, record_output = create_output_recorder()

    result = run_talk_to_companion(
        conversation_history,
        create_memories(),
        input_function=lambda prompt: "Unanswered question",
        print_function=record_output,
        response_function=failed_response,
        provider_used_function=unexpected_provider_lookup,
    )

    assert result["status"] == "failed"
    assert result["provider"] is None
    assert conversation_history == original_history
    assert "Could not connect to Ollama." in messages
    assert "Diagnostic: ollama/connection" in messages


def test_provider_flow_displays_current_provider_information():
    messages, record_output = create_output_recorder()

    result = run_view_ai_provider(
        print_function=record_output,
        provider_info_function=lambda: {
            "provider": "ollama",
            "model": "qwen3:4b-instruct",
            "type": "local",
        },
    )

    assert result["status"] == "available"
    assert "Active provider: ollama" in messages
    assert "Model: qwen3:4b-instruct" in messages
    assert "Type: local" in messages


def test_provider_flow_reports_invalid_configuration():
    def invalid_provider():
        raise ProviderError(
            provider="config",
            kind="invalid_provider",
            message="Invalid AI provider configuration.",
            retryable=False,
            fallback_allowed=False,
        )

    messages, record_output = create_output_recorder()

    result = run_view_ai_provider(
        print_function=record_output,
        provider_info_function=invalid_provider,
    )

    assert result["status"] == "failed"
    assert result["provider_info"] is None
    assert "Could not read AI provider configuration." in messages
    assert "Diagnostic: config/invalid_provider" in messages


@pytest.mark.parametrize("confirmation", ["yes", "YES", " yes "])
def test_clear_and_status_flows_share_mutable_conversation_state(confirmation):
    conversation_history = [
        {"role": "user", "content": "Question"},
        {"role": "assistant", "content": "Answer"},
    ]
    messages, record_output = create_output_recorder()
    original = deepcopy(conversation_history)
    shared_history = conversation_history
    prompts = []

    def confirm_clear(prompt):
        prompts.append(prompt)
        assert conversation_history == original
        assert "--- Clear Conversation Preview ---" in messages
        assert "Messages to clear: 2" in messages
        assert (
            "Only this session's chat will be cleared; saved memories stay."
            in messages
        )
        assert "This cannot be undone within this session." in messages
        return confirmation

    before = run_view_conversation_status(
        conversation_history,
        print_function=record_output,
    )
    cleared = run_clear_conversation(
        conversation_history,
        print_function=record_output,
        input_function=confirm_clear,
    )
    after = run_view_conversation_status(
        conversation_history,
        print_function=record_output,
    )

    assert before["message_count"] == 2
    assert cleared == {
        "status": "cleared",
        "message_count": 0,
    }
    assert after["message_count"] == 0
    assert conversation_history == []
    assert shared_history is conversation_history
    assert len(prompts) == 1
    assert "Conversation history cleared." in messages


@pytest.mark.parametrize("confirmation", ["no", "", "y", "yes please"])
def test_cancel_clear_preserves_conversation_and_status(confirmation):
    conversation_history = [
        {"role": "user", "content": "Keep my question"},
        {"role": "assistant", "content": "Keep this answer"},
    ]
    original = deepcopy(conversation_history)
    messages, record_output = create_output_recorder()

    result = run_clear_conversation(
        conversation_history,
        print_function=record_output,
        input_function=lambda prompt: confirmation,
    )

    assert result == {"status": "cancelled", "message_count": 2}
    assert conversation_history == original
    assert run_view_conversation_status(
        conversation_history, print_function=record_output
    )["message_count"] == 2
    assert "Cancelled. Conversation history was not changed." in messages
    assert "Conversation history cleared." not in messages


@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt])
def test_interrupted_confirmation_does_not_clear_conversation(interruption):
    conversation_history = [{"role": "user", "content": "Keep this"}]
    original = deepcopy(conversation_history)
    messages, record_output = create_output_recorder()

    def interrupted_input(prompt):
        raise interruption()

    result = run_clear_conversation(
        conversation_history,
        print_function=record_output,
        input_function=interrupted_input,
    )

    assert result == {"status": "cancelled", "message_count": 1}
    assert conversation_history == original
    assert "Cancelled. Conversation history was not changed." in messages


def test_empty_conversation_does_not_ask_for_confirmation():
    conversation_history = []
    messages, record_output = create_output_recorder()

    def unexpected_input(prompt):
        pytest.fail("There is no conversation to clear.")

    result = run_clear_conversation(
        conversation_history,
        print_function=record_output,
        input_function=unexpected_input,
    )

    assert result == {"status": "empty", "message_count": 0}
    assert conversation_history == []
    assert "Conversation history is already empty." in messages
    assert "--- Clear Conversation Preview ---" not in messages


@pytest.mark.parametrize("confirmation", ["yes", "no"])
def test_main_clear_confirmation_controls_next_chat_without_changing_files(
    tmp_path,
    monkeypatch,
    capsys,
    confirmation,
):
    data_directory = tmp_path / "src" / "solitude_kaizen" / "data"
    memory_path = data_directory / "memories.json"
    profile_path = data_directory / "profile.json"
    database_path = data_directory / "solitude_kaizen.db"
    memory_data = {"memories": create_memories()}
    ensure_json_file(memory_path, memory_data)
    ensure_json_file(profile_path, {"user_name": "Test User"})
    initialize_database(database_path)
    original_files = {
        path: path.read_bytes()
        for path in (memory_path, profile_path, database_path)
    }
    saved = []
    save_function = memory.save_memories

    def record_save(path, data):
        saved.append(deepcopy(data))
        save_function(path, data)

    answers = iter([
        "12", "First test question", "14", confirmation, "15",
        "12", "Second test question", "27",
    ])
    prompts = []

    def read_input(prompt):
        prompts.append(prompt)
        return next(answers)

    requests = []

    def fake_response(system_prompt, user_message):
        requests.append((system_prompt, user_message))
        return f"Test reply {len(requests)}"

    monkeypatch.setattr(memory, "save_memories", record_save)
    monkeypatch.setattr("builtins.input", read_input)
    monkeypatch.setattr(
        conversation_cli,
        "run_talk_to_companion",
        partial(
            conversation_cli.run_talk_to_companion,
            input_function=read_input,
            response_function=fake_response,
            provider_used_function=lambda: "test",
        ),
    )
    monkeypatch.setenv("SK_RESEARCH_ENABLED", "false")
    monkeypatch.setenv("KAIZEN_DISCOVERY_ENABLED", "false")
    monkeypatch.setenv("SK_CONTINUOUS_LEARNING_ENABLED", "false")
    monkeypatch.chdir(tmp_path)

    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")

    output = capsys.readouterr().out
    assert len(requests) == 2
    assert "Messages to clear: 2" in output
    assert sum("Type 'yes'" in prompt for prompt in prompts) == 1
    assert "Goodbye!" in output
    assert state["memories"] == memory_data["memories"]
    # The existing startup normalization saves once; clearing must not save.
    assert saved == [memory_data]
    for path, original_bytes in original_files.items():
        assert path.read_bytes() == original_bytes

    if confirmation == "yes":
        assert "Conversation history cleared." in output
        assert "Messages in short-term history: 0" in output
        assert "First test question" not in requests[1][0]
        assert "Test reply 1" not in requests[1][0]
        assert len(state["conversation_history"]) == 2
    else:
        assert "Cancelled. Conversation history was not changed." in output
        assert "Messages in short-term history: 2" in output
        assert "First test question" in requests[1][0]
        assert "Test reply 1" in requests[1][0]
        assert len(state["conversation_history"]) == 4
