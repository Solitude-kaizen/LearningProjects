import pytest
import requests

from src.solitude_kaizen.memory import (
    load_memories,
    save_memories,
    create_memory,
    search_memories,
    forget_memory,
    format_memory,
    validate_importance,
    validate_category,
    normalize_memory,
    filter_memories_by_category,
    sort_memories_by_importance,
    sort_memories_by_recency,
    rank_memories,
    select_memories_for_context,
    build_memory_context,
)

from src.solitude_kaizen.conversation import (
    build_conversation_context,
    trim_conversation_history,
    create_conversation_message,
    add_message_to_history,
    record_assistant_response,
    prepare_user_turn,
)

from src.solitude_kaizen.ai_service import (
    generate_response,
    generate_groq_response,
    generate_ollama_response,
    generate_openai_response,
    get_last_provider_used,
    get_active_provider,
    get_provider_info,
    OPENAI_TIMEOUT_SECONDS,
    GROQ_TIMEOUT_SECONDS,
    OLLAMA_TIMEOUT_SECONDS,
    ProviderError,
)

from src.solitude_kaizen.prompt import build_system_prompt

def test_validate_importance():
    assert validate_importance("1") == 1
    assert validate_importance("3") == 3
    assert validate_importance("5") == 5

    assert validate_importance("0") is None
    assert validate_importance("6") is None
    assert validate_importance("banana") is None

def test_validate_category():
    assert validate_category("learning") == "learning"
    assert validate_category("PROJECT") == "project"
    assert validate_category(" health ") == "health"

    assert validate_category("banana") is None
    assert validate_category("123") is None

def test_normalize_memory_from_string():
    memory = normalize_memory("Learn Python")

    assert memory["text"] == "Learn Python"
    assert memory["category"] == "personal"
    assert memory["importance"] == 3
    assert memory["created_at"] == "unknown"


def test_normalize_memory_from_dict():
    memory = normalize_memory(
        {
            "text": "Finish project",
            "category": " project",
            "importance": "5"
        }
    )

    assert memory["text"] == "Finish project"
    assert memory["category"] == "project"
    assert memory["importance"] == 5
    assert memory["created_at"] == "unknown"

def test_create_memory():
    memory = create_memory(
        "Study Python",
        "learning",
        4
    )

    assert memory["text"] == "Study Python"
    assert memory["category"] == "learning"
    assert memory["importance"] == 4
    assert "created_at" in memory

def test_search_memories():
    memories = [
        {
            "text": "Study Python",
            "category": "learning",
            "importance": 4,
            "created_at": "unknown"
        },
        {
            "text": "Build HR career",
            "category": "career",
            "importance": 5,
            "created_at": "unknown"
        }
    ]

    matches = search_memories(memories, "python")

    assert len(matches) == 1
    assert matches[0]["text"] == "Study Python"

    matches = search_memories(memories, "career")

    assert len(matches) == 1
    assert matches[0]["text"] == "Build HR career"

def test_forget_memory():
    memories = [
        {
            "text": "Study Python",
            "category": "learning",
            "importance": 4,
            "created_at": "unknown"
        },
        {
            "text": "Build HR career",
            "category": "career",
            "importance": 5,
            "created_at": "unknown"
        }
    ]

    forgotten = forget_memory(memories, 0)

    assert forgotten["text"] == "Study Python"
    assert len(memories) == 1
    assert memories[0]["text"] == "Build HR career"

def test_forget_memory_invalid_index():
    memories = [
        {
            "text": "Study Python",
            "category": "learning",
            "importance": 4,
            "created_at": "unknown"
        }
    ]

    forgotten = forget_memory(memories, 5)

    assert forgotten is None
    assert len(memories) == 1

def test_save_and_load_memories(tmp_path):
    memory_path = tmp_path / "memories.json"

    memory_data = {
        "memories": [
            {
                "text": "Test persistence",
                "category": "test",
                "importance": 4,
                "created_at": "unknown"
            }
        ]
    }

    save_memories(memory_path, memory_data)

    loaded_data = load_memories(memory_path)

    assert loaded_data == memory_data

def test_format_memory():
    memory = {
        "text": "Study Python",
        "category": "learning",
        "importance": 4,
        "created_at": "2026-08-17T16:00:00"
    }

    formatted = format_memory(memory)

    assert formatted == (
        "Study Python "
        "[Category: learning "
        "| Importance: 4 "
        "| Created At: 2026-08-17T16:00:00]"
    )

def test_filter_memories_by_category():
    memories = [
        {
            "text": "Study Python",
            "category": "learning",
            "importance": 4,
            "created_at": "unknown"
        },
        {
            "text": "Build HR career",
            "category": "career",
            "importance": 5,
            "created_at": "unknown"
        },
        {
            "text": "Practice Python",
            "category": "learning",
            "importance": 3,
            "created_at": "unknown"
        }
    ]

    matches = filter_memories_by_category(
        memories,
        "learning"
    )

    assert len(matches) == 2
    assert matches[0]["text"] == "Study Python"
    assert matches[1]["text"] == "Practice Python"

def test_sort_memories_by_importance():
    memories = [
        {
            "text": "Low priority",
            "category": "personal",
            "importance": 1,
            "created_at": "unknown"
        },
        {
            "text": "High priority",
            "category": "project",
            "importance": 5,
            "created_at": "unknown"
        },
        {
            "text": "Medium priority",
            "category": "learning",
            "importance": 3,
            "created_at": "unknown"
        }
    ]

    sorted_memories = sort_memories_by_importance(memories)

    assert sorted_memories[0]["importance"] == 5
    assert sorted_memories[1]["importance"] == 3
    assert sorted_memories[2]["importance"] == 1

def test_sort_memories_by_recency():
    memories = [
        {
            "text": "Old legacy memory",
            "category": "personal",
            "importance": 3,
            "created_at": "unknown"
        },
        {
            "text": "Older memory",
            "category": "learning",
            "importance": 4,
            "created_at": "2026-08-15T10:00:00"
        },
        {
            "text": "Newest memory",
            "category": "project",
            "importance": 5,
            "created_at": "2026-08-17T17:00:00"
        }
    ]

    sorted_memories = sort_memories_by_recency(memories)

    assert sorted_memories[0]["text"] == "Newest memory"
    assert sorted_memories[1]["text"] == "Older memory"
    assert sorted_memories[2]["text"] == "Old legacy memory"

def test_rank_memories():
    memories = [
        {
            "text": "Old important memory",
            "category": "project",
            "importance": 5,
            "created_at": "2026-08-15T10:00:00"
        },
        {
            "text": "New important memory",
            "category": "project",
            "importance": 5,
            "created_at": "2026-08-17T17:00:00"
        },
        {
            "text": "Recent lower-priority memory",
            "category": "learning",
            "importance": 4,
            "created_at": "2026-08-17T18:00:00"
        }
    ]

    ranked = rank_memories(memories)

    assert ranked[0]["text"] == "New important memory"
    assert ranked[1]["text"] == "Old important memory"
    assert ranked[2]["text"] == "Recent lower-priority memory"

def test_select_memories_for_context():

    memories = [
        {
            "text": "Memory A",
            "category": "personal",
            "importance": 2,
            "created_at": "2026-08-15T10:00:00"
        },
        {
            "text": "Memory B",
            "category": "project",
            "importance": 5,
            "created_at": "2026-08-17T10:00:00"
        },
        {
            "text": "Memory C",
            "category": "learning",
            "importance": 4,
            "created_at": "2026-08-17T09:00:00"
        },
        {
            "text": "Memory D",
            "category": "career",
            "importance": 3,
            "created_at": "2026-08-16T10:00:00"
        }
    ]

    selected = select_memories_for_context(
        memories,
        limit=2
    )

    assert len(selected) == 2
    assert selected[0]["text"] == "Memory B"
    assert selected[1]["text"] == "Memory C"

def test_build_memory_context():
    memories = [
        {
            "text": "Finish Solitude-Kaizen V1",
            "category": "project",
            "importance": 5,
            "created_at": "2026-08-17T10:00:00"
        },
        {
            "text": "Practice Python",
            "category": "learning",
            "importance": 4,
            "created_at": "2026-08-17T09:00:00"
        }
    ]

    context = build_memory_context(
        memories,
        limit=2
    )

    assert "Finish Solitude-Kaizen V1" in context
    assert "Practice Python" in context
    assert "category: project" in context
    assert "importance: 5" in context

def test_build_system_prompt():
    memory_context = (
        "- Finish Solitude-Kaizen V1 "
        "(category: project, importance: 5)"
    )

    prompt = build_system_prompt(memory_context)

    assert "You are Solitude-Kaizen" in prompt
    assert "Relevant memories:" in prompt
    assert "Finish Solitude-Kaizen V1" in prompt
    assert "Do not force memories" in prompt

def test_generate_response_uses_groq(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "groq")

    def fake_groq_response(system_prompt, user_message):
        return f"Mock response to: {user_message}"

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_groq_response",
        fake_groq_response
    )

    response = generate_response(
        "System prompt",
        "Hello"
    )

    assert response == "Mock response to: Hello"
def test_generate_ollama_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "response": "Mock local response"
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.requests.post",
        fake_post
    )

    response = generate_ollama_response(
        "System prompt",
        "Hello"
    )

    assert response == "Mock local response"

def test_generate_response_falls_back_when_groq_key_is_missing(
    monkeypatch
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "groq",
    )

    def fake_groq_response(
        system_prompt,
        user_message,
    ):
        raise ProviderError(
            provider="groq",
            kind="missing_api_key",
            message="Groq API key is not configured yet.",
            retryable=False,
            fallback_allowed=True,
        )

    def fake_ollama_response(
        system_prompt,
        user_message,
    ):
        return "Local fallback response"

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_groq_response",
        fake_groq_response,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_ollama_response",
        fake_ollama_response,
    )

    response = generate_response(
        "System prompt",
        "Hello",
    )

    provider = get_last_provider_used()

    assert response == "Local fallback response"
    assert provider == "ollama"


def test_provider_tracking_records_groq(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "groq")

    def fake_groq_response(system_prompt, user_message):
        return "Mock Groq response"

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_groq_response",
        fake_groq_response
    )

    response = generate_response(
        "System prompt",
        "Hello"
    )

    provider = get_last_provider_used()

    assert response == "Mock Groq response"
    assert provider == "groq"

def test_get_active_provider_from_env(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")

    provider = get_active_provider()

    assert provider == "ollama"

def test_build_conversation_context():
    conversation_history = [
        {
            "role": "user",
            "content": "Teach me Python loops."
        },
        {
            "role": "assistant",
            "content": "A loop repeats code."
        }
    ]

    context = build_conversation_context(
        conversation_history,
        limit=6
    )

    assert "User: Teach me Python loops." in context
    assert "Assistant: A loop repeats code." in context

def test_build_system_prompt_with_conversation():
    memory_context = "- Learn Python"
    conversation_context = (
        "User: Teach me loops.\n"
        "Assistant: A loop repeats code."
    )

    prompt = build_system_prompt(
        memory_context,
        conversation_context
    )

    assert "Relevant memories:" in prompt
    assert "Recent conversation:" in prompt
    assert "User: Teach me loops." in prompt
    assert "Assistant: A loop repeats code." in prompt

def test_trim_conversation_history():
    conversation_history = [
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Message 2"},
        {"role": "user", "content": "Message 3"},
        {"role": "assistant", "content": "Message 4"},
        {"role": "user", "content": "Message 5"},
    ]

    trimmed = trim_conversation_history(
        conversation_history,
        limit=3
    )

    assert len(trimmed) == 3
    assert trimmed[0]["content"] == "Message 3"
    assert trimmed[1]["content"] == "Message 4"
    assert trimmed[2]["content"] == "Message 5"

def test_create_conversation_message():
    message = create_conversation_message(
        "user",
        "Hello"
    )

    assert message == {
        "role": "user",
        "content": "Hello",
    }

def test_add_message_to_history():
    conversation_history = []

    message = add_message_to_history(
        conversation_history,
        "user",
        "Hello"
    )

    assert message == {
        "role": "user",
        "content": "Hello",
    }

    assert conversation_history == [
        {
            "role": "user",
            "content": "Hello",
        }
    ]

def test_record_assistant_response():
    conversation_history = [
        {
            "role": "user",
            "content": "Hello"
        }
    ]

    record_assistant_response(
        conversation_history,
        "Hi there",
        limit=2
    )

    assert len(conversation_history) == 2
    assert conversation_history[1] == {
        "role": "assistant",
        "content": "Hi there",
    }


def test_prepare_user_turn():
    conversation_history = [
        {
            "role": "user",
            "content": "What is Python?"
        },
        {
            "role": "assistant",
            "content": "Python is a programming language."
        }
    ]

    conversation_context = prepare_user_turn(
        conversation_history,
        "Can you explain that more simply?"
    )

    assert "What is Python?" in conversation_context
    assert "Python is a programming language." in conversation_context
    assert "Can you explain that more simply?" not in conversation_context

    assert conversation_history[-1] == {
        "role": "user",
        "content": "Can you explain that more simply?"
    }

def test_generate_openai_response_raises_provider_error_on_unknown_error(
    monkeypatch,
    capsys,
):
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-key",
    )

    class FakeOpenAI:
        def __init__(
            self,
            api_key,
            timeout=None,
        ):
            raise RuntimeError(
                "Simulated OpenAI failure"
        )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAI",
        FakeOpenAI,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_openai_response(
            "System prompt",
            "Hello",
        )

    captured = capsys.readouterr()
    error = error_info.value

    assert error.provider == "openai"
    assert error.kind == "unknown"
    assert error.retryable is False
    assert error.fallback_allowed is False
    assert str(error) == "Unexpected OpenAI error."

    assert "OpenAI unexpected error:" in captured.out
    assert "RuntimeError" in captured.out
    assert "Simulated OpenAI failure" not in captured.out

def test_provider_error_stores_details():
    error = ProviderError(
        provider="groq",
        kind="rate_limit",
        message="Too many requests",
        retryable=True,
    )

    assert str(error) == "Too many requests"
    assert error.provider == "groq"
    assert error.kind == "rate_limit"
    assert error.retryable is True


def test_generate_groq_response_raises_provider_error_without_key(
    monkeypatch
):
    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_groq_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "groq"
    assert error.kind == "missing_api_key"
    assert error.retryable is False
    assert str(error) == (
        "Groq API key is not configured yet."
    )

def test_generate_groq_response_raises_provider_error_on_rate_limit(
    monkeypatch
):
    class FakeRateLimitError(Exception):
        pass

    class FakeCompletions:
        def create(self, *args, **kwargs):
            raise FakeRateLimitError(
                "Simulated Groq rate limit"
            )

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeGroq:
        def __init__(self, *args, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.RateLimitError",
        FakeRateLimitError,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.Groq",
        FakeGroq,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_groq_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_groq_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "groq"
    assert error.kind == "rate_limit"
    assert error.retryable is True
    assert str(error) == (
        "Groq rate limit reached."
    )

def test_generate_response_falls_back_when_fallback_allowed(
    monkeypatch
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "groq",
    )

    def fake_groq_response(
        system_prompt,
        user_message,
    ):
        raise ProviderError(
            provider="groq",
            kind="rate_limit",
            message="Groq rate limit reached.",
            retryable=True,
            fallback_allowed=True,
        )

    def fake_ollama_response(
        system_prompt,
        user_message,
    ):
        return "Local fallback response"

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_groq_response",
        fake_groq_response,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_ollama_response",
        fake_ollama_response,
    )

    response = generate_response(
        "System prompt",
        "Hello",
    )

    provider = get_last_provider_used()

    assert response == "Local fallback response"
    assert provider == "ollama"

def test_generate_response_does_not_fallback_on_non_retryable_error(
    monkeypatch
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "groq",
    )

    ollama_called = False

    def fake_groq_response(
        system_prompt,
        user_message,
    ):
        raise ProviderError(
            provider="groq",
            kind="bad_request",
            message="Invalid Groq request.",
            retryable=False,
        )

    def fake_ollama_response(
        system_prompt,
        user_message,
    ):
        nonlocal ollama_called
        ollama_called = True

        return "This should not be used"

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_groq_response",
        fake_groq_response,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_ollama_response",
        fake_ollama_response,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "groq"
    assert error.kind == "bad_request"
    assert error.retryable is False
    assert ollama_called is False

def test_provider_error_stores_fallback_policy():
    default_error = ProviderError(
        provider="groq",
        kind="bad_request",
        message="Invalid request.",
        retryable=False,
    )

    fallback_error = ProviderError(
        provider="groq",
        kind="authentication",
        message="Authentication failed.",
        retryable=False,
        fallback_allowed=True,
    )

    assert default_error.fallback_allowed is False
    assert fallback_error.fallback_allowed is True

def test_generate_groq_response_raises_provider_error_on_authentication(
    monkeypatch
):
    class FakeAuthenticationError(Exception):
        pass

    class FakeCompletions:
        def create(self, *args, **kwargs):
            raise FakeAuthenticationError(
                "Simulated Groq authentication failure"
            )

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeGroq:
        def __init__(self, *args, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.AuthenticationError",
        FakeAuthenticationError,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.Groq",
        FakeGroq,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_groq_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_groq_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "groq"
    assert error.kind == "authentication"
    assert error.retryable is False
    assert error.fallback_allowed is True
    assert str(error) == (
        "Groq authentication failed."
    )

def test_generate_groq_response_raises_provider_error_on_permission_denied(
    monkeypatch
):
    class FakePermissionDeniedError(Exception):
        pass

    class FakeCompletions:
        def create(self, *args, **kwargs):
            raise FakePermissionDeniedError(
                "Simulated Groq permission failure"
            )

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeGroq:
        def __init__(self, *args, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.PermissionDeniedError",
        FakePermissionDeniedError,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.Groq",
        FakeGroq,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_groq_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_groq_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "groq"
    assert error.kind == "permission_denied"
    assert error.retryable is False
    assert error.fallback_allowed is True
    assert str(error) == (
        "Groq permission denied."
    )

def test_generate_groq_response_raises_provider_error_on_bad_request(
    monkeypatch
):
    class FakeBadRequestError(Exception):
        pass

    class FakeCompletions:
        def create(self, *args, **kwargs):
            raise FakeBadRequestError(
                "Simulated Groq bad request"
            )

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeGroq:
        def __init__(self, *args, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.BadRequestError",
        FakeBadRequestError,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.Groq",
        FakeGroq,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_groq_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_groq_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "groq"
    assert error.kind == "bad_request"
    assert error.retryable is False
    assert error.fallback_allowed is False
    assert str(error) == (
        "Groq rejected the request."
    )

def test_generate_groq_response_raises_provider_error_on_unknown_error(
    monkeypatch,
    capsys,
):
    class FakeCompletions:
        def create(self, *args, **kwargs):
            raise RuntimeError(
                "Simulated Groq failure"
            )

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeGroq:
        def __init__(self, *args, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.Groq",
        FakeGroq,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_groq_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_groq_response(
            "System prompt",
            "Hello",
        )

    captured = capsys.readouterr()
    error = error_info.value

    assert error.provider == "groq"
    assert error.kind == "unknown"
    assert error.retryable is False
    assert error.fallback_allowed is False
    assert str(error) == "Unexpected Groq error."

    assert "Groq unexpected error:" in captured.out
    assert "RuntimeError" in captured.out
    assert "Simulated Groq failure" not in captured.out

def test_generate_openai_response_raises_provider_error_without_key(
    monkeypatch
):
    monkeypatch.delenv(
        "OPENAI_API_KEY",
        raising=False,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_openai_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "openai"
    assert error.kind == "missing_api_key"
    assert error.retryable is False
    assert error.fallback_allowed is True
    assert str(error) == (
        "OpenAI API key is not configured yet."
    )

def test_generate_response_falls_back_from_openai_when_allowed(
    monkeypatch
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "openai",
    )

    def fake_openai_response(
        system_prompt,
        user_message,
    ):
        raise ProviderError(
            provider="openai",
            kind="missing_api_key",
            message="OpenAI API key is not configured yet.",
            retryable=False,
            fallback_allowed=True,
        )

    def fake_ollama_response(
        system_prompt,
        user_message,
    ):
        return "Local fallback response"

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_openai_response",
        fake_openai_response,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_ollama_response",
        fake_ollama_response,
    )

    response = generate_response(
        "System prompt",
        "Hello",
    )

    provider = get_last_provider_used()

    assert response == "Local fallback response"
    assert provider == "ollama"

def test_generate_openai_response_raises_provider_error_on_rate_limit(
    monkeypatch
):
    class FakeOpenAIRateLimitError(Exception):
        pass

    class FakeResponses:
        def create(self, *args, **kwargs):
            raise FakeOpenAIRateLimitError(
                "Simulated OpenAI rate limit"
            )

    class FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAIRateLimitError",
        FakeOpenAIRateLimitError,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAI",
        FakeOpenAI,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_openai_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_openai_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "openai"
    assert error.kind == "rate_limit"
    assert error.retryable is True
    assert error.fallback_allowed is True
    assert str(error) == (
        "OpenAI rate limit reached."
    )

def test_generate_openai_response_raises_provider_error_on_authentication(
    monkeypatch
):
    class FakeOpenAIAuthenticationError(Exception):
        pass

    class FakeResponses:
        def create(self, *args, **kwargs):
            raise FakeOpenAIAuthenticationError(
                "Simulated OpenAI authentication failure"
            )

    class FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAIAuthenticationError",
        FakeOpenAIAuthenticationError,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAI",
        FakeOpenAI,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_openai_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_openai_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "openai"
    assert error.kind == "authentication"
    assert error.retryable is False
    assert error.fallback_allowed is True
    assert str(error) == (
        "OpenAI authentication failed."
    )

def test_generate_openai_response_raises_provider_error_on_permission_denied(
    monkeypatch
):
    class FakeOpenAIPermissionDeniedError(Exception):
        pass

    class FakeResponses:
        def create(self, *args, **kwargs):
            raise FakeOpenAIPermissionDeniedError(
                "Simulated OpenAI permission failure"
            )

    class FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAIPermissionDeniedError",
        FakeOpenAIPermissionDeniedError,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAI",
        FakeOpenAI,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_openai_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_openai_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "openai"
    assert error.kind == "permission_denied"
    assert error.retryable is False
    assert error.fallback_allowed is True
    assert str(error) == (
        "OpenAI permission denied."
    )

def test_generate_openai_response_raises_provider_error_on_bad_request(
    monkeypatch
):
    class FakeOpenAIBadRequestError(Exception):
        pass

    class FakeResponses:
        def create(self, *args, **kwargs):
            raise FakeOpenAIBadRequestError(
                "Simulated OpenAI bad request"
            )

    class FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAIBadRequestError",
        FakeOpenAIBadRequestError,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAI",
        FakeOpenAI,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.get_openai_api_key",
        lambda: "fake-key",
    )

    with pytest.raises(ProviderError) as error_info:
        generate_openai_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "openai"
    assert error.kind == "bad_request"
    assert error.retryable is False
    assert error.fallback_allowed is False
    assert str(error) == (
        "OpenAI rejected the request."
    )

def test_generate_ollama_response_raises_provider_error_on_connection(
    monkeypatch
):
    def fake_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError(
            "Simulated Ollama connection failure"
        )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.requests.post",
        fake_post,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_ollama_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "ollama"
    assert error.kind == "connection"
    assert error.retryable is True
    assert error.fallback_allowed is False
    assert str(error) == (
        "Could not connect to Ollama."
    )

def test_generate_ollama_response_raises_provider_error_on_timeout(
    monkeypatch
):
    def fake_post(*args, **kwargs):
        raise requests.exceptions.Timeout(
            "Simulated Ollama timeout"
        )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.requests.post",
        fake_post,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_ollama_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "ollama"
    assert error.kind == "timeout"
    assert error.retryable is True
    assert error.fallback_allowed is False
    assert str(error) == (
        "Ollama request timed out."
    )

def test_generate_ollama_response_raises_provider_error_on_server_error(
    monkeypatch
):
    class FakeResponse:
        status_code = 500

        def raise_for_status(self):
            error = requests.exceptions.HTTPError(
                "Simulated Ollama server error"
            )
            error.response = self
            raise error

        def json(self):
            return {
                "response": "Should not be reached"
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.requests.post",
        fake_post,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_ollama_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "ollama"
    assert error.kind == "server_error"
    assert error.retryable is True
    assert error.fallback_allowed is False
    assert str(error) == (
        "Ollama server error."
    )

def test_generate_ollama_response_raises_provider_error_on_http_error(
    monkeypatch
):
    class FakeResponse:
        status_code = 400

        def raise_for_status(self):
            error = requests.exceptions.HTTPError(
                "Simulated Ollama bad request"
            )
            error.response = self
            raise error

        def json(self):
            return {
                "response": "Should not be reached"
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.requests.post",
        fake_post,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_ollama_response(
            "System prompt",
            "Hello",
        )

    error = error_info.value

    assert error.provider == "ollama"
    assert error.kind == "http_error"
    assert error.retryable is False
    assert error.fallback_allowed is False
    assert str(error) == (
        "Ollama rejected the request."
    )

def test_generate_ollama_response_raises_provider_error_on_unknown_error(
    monkeypatch,
    capsys,
):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {}

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.requests.post",
        fake_post,
    )

    with pytest.raises(ProviderError) as error_info:
        generate_ollama_response(
            "System prompt",
            "Hello",
        )

    captured = capsys.readouterr()
    error = error_info.value

    assert error.provider == "ollama"
    assert error.kind == "unknown"
    assert error.retryable is False
    assert error.fallback_allowed is False
    assert str(error) == "Unexpected Ollama error."

    assert "Ollama unexpected error:" in captured.out
    assert "KeyError" in captured.out

def test_generate_response_returns_unavailable_when_groq_and_ollama_fail(
    monkeypatch
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "groq",
    )

    def fake_groq_response(
        system_prompt,
        user_message,
    ):
        raise ProviderError(
            provider="groq",
            kind="rate_limit",
            message="Groq rate limit reached.",
            retryable=True,
            fallback_allowed=True,
        )

    def fake_ollama_response(
        system_prompt,
        user_message,
    ):
        raise ProviderError(
            provider="ollama",
            kind="connection",
            message="Could not connect to Ollama.",
            retryable=True,
            fallback_allowed=False,
        )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_groq_response",
        fake_groq_response,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_ollama_response",
        fake_ollama_response,
    )

    response = generate_response(
        "System prompt",
        "Hello",
    )

    provider = get_last_provider_used()

    assert response == (
        "All available AI providers are currently unavailable."
    )
    assert provider is None

def test_generate_response_returns_unavailable_when_openai_and_ollama_fail(
    monkeypatch
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "openai",
    )

    def fake_openai_response(
        system_prompt,
        user_message,
    ):
        raise ProviderError(
            provider="openai",
            kind="rate_limit",
            message="OpenAI rate limit reached.",
            retryable=True,
            fallback_allowed=True,
        )

    def fake_ollama_response(
        system_prompt,
        user_message,
    ):
        raise ProviderError(
            provider="ollama",
            kind="connection",
            message="Could not connect to Ollama.",
            retryable=True,
            fallback_allowed=False,
        )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_openai_response",
        fake_openai_response,
    )

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.generate_ollama_response",
        fake_ollama_response,
    )

    response = generate_response(
        "System prompt",
        "Hello",
    )

    provider = get_last_provider_used()

    assert response == (
        "All available AI providers are currently unavailable."
    )
    assert provider is None

def test_get_active_provider_raises_provider_error_on_invalid_provider(
    monkeypatch
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "banana",
    )

    with pytest.raises(ProviderError) as error_info:
        get_active_provider()

    error = error_info.value

    assert error.provider == "config"
    assert error.kind == "invalid_provider"
    assert error.retryable is False
    assert error.fallback_allowed is False
    assert str(error) == "Invalid AI provider configuration."

def test_get_provider_info_raises_provider_error_on_invalid_provider(
    monkeypatch
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "banana",
    )

    with pytest.raises(ProviderError) as error_info:
        get_provider_info()

    error = error_info.value

    assert error.provider == "config"
    assert error.kind == "invalid_provider"
    assert error.retryable is False
    assert error.fallback_allowed is False

def test_generate_openai_response_uses_configured_timeout(
    monkeypatch
):
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-key",
    )

    captured_timeout = {}

    class FakeResponse:
        output_text = "Test response"

    class FakeResponses:
        def create(
            self,
            model,
            instructions,
            input,
        ):
            return FakeResponse()

    class FakeOpenAI:
        def __init__(
            self,
            api_key,
            timeout=None,
        ):
            captured_timeout["value"] = timeout
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.OpenAI",
        FakeOpenAI,
    )

    response = generate_openai_response(
        "System prompt",
        "Hello",
    )

    assert response == "Test response"
    assert captured_timeout["value"] == OPENAI_TIMEOUT_SECONDS

def test_generate_groq_response_uses_configured_timeout(
    monkeypatch
):
    monkeypatch.setenv(
        "GROQ_API_KEY",
        "test-key",
    )

    captured_timeout = {}

    class FakeMessage:
        content = "Test response"

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(
            self,
            model,
            messages,
        ):
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeGroq:
        def __init__(
            self,
            api_key,
            timeout=None,
        ):
            captured_timeout["value"] = timeout
            self.chat = FakeChat()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.Groq",
        FakeGroq,
    )

    response = generate_groq_response(
        "System prompt",
        "Hello",
    )

    assert response == "Test response"
    assert captured_timeout["value"] == GROQ_TIMEOUT_SECONDS

def test_generate_ollama_response_uses_configured_timeout(
    monkeypatch
):
    captured_timeout = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "response": "Test response",
            }

    def fake_post(
        url,
        json,
        timeout=None,
    ):
        captured_timeout["value"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        "src.solitude_kaizen.ai_service.requests.post",
        fake_post,
    )

    response = generate_ollama_response(
        "System prompt",
        "Hello",
    )

    assert response == "Test response"
    assert captured_timeout["value"] == OLLAMA_TIMEOUT_SECONDS

