import pytest

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


def test_clear_and_status_flows_share_mutable_conversation_state():
    conversation_history = [
        {"role": "user", "content": "Question"},
        {"role": "assistant", "content": "Answer"},
    ]
    messages, record_output = create_output_recorder()

    before = run_view_conversation_status(
        conversation_history,
        print_function=record_output,
    )
    cleared = run_clear_conversation(
        conversation_history,
        print_function=record_output,
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
    assert "Conversation history cleared." in messages
