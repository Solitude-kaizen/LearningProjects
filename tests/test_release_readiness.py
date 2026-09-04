import runpy
import socket

import pytest

from src.solitude_kaizen import ai_service
from src.solitude_kaizen.memory import load_memories, load_profile


def test_first_run_without_keys_or_network_supports_local_status_and_empty_views(
    tmp_path,
    monkeypatch,
    capsys,
):
    """Exercise real menu wiring in an empty directory, not personal data."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("SK_RESEARCH_ENABLED", "false")
    monkeypatch.setenv("KAIZEN_DISCOVERY_ENABLED", "false")
    monkeypatch.setenv("SK_CONTINUOUS_LEARNING_ENABLED", "false")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def unexpected_request(*args, **kwargs):
        pytest.fail(
            "First-run status and empty views must not request inference or network."
        )

    monkeypatch.setattr(socket.socket, "connect", unexpected_request)
    monkeypatch.setattr(socket.socket, "connect_ex", unexpected_request)
    for provider in ("ollama", "groq", "openai"):
        monkeypatch.setattr(
            ai_service, f"generate_{provider}_response", unexpected_request
        )

    answers = iter(["3", "5", "13", "15", "18", "25", "27"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")

    output = capsys.readouterr().out
    assert "Hello, User." in output
    assert "--- My Profile ---" in output
    assert "I do not have any memories saved yet." in output
    assert "Active provider: ollama" in output
    assert "Messages in short-term history: 0" in output
    assert "No public research has been collected yet." in output
    assert "No continuity backup is available yet." in output
    assert "Reflection question:" not in output
    assert "Goodbye!" in output
    assert state["conversation_history"] == []
    assert state["startup_result"]["status"] == "disabled"

    data_directory = tmp_path / "src" / "solitude_kaizen" / "data"
    assert load_profile(data_directory / "profile.json")["user_name"] == "User"
    assert load_memories(data_directory / "memories.json") == {"memories": []}
    assert not (data_directory / "backups").exists()
    assert not (tmp_path / ".env").exists()
