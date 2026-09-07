from copy import deepcopy
import runpy

import pytest

from src.solitude_kaizen import memory_cli
from src.solitude_kaizen.database import initialize_database
from src.solitude_kaizen.memory import ensure_json_file


def sample_memories():
    return [
        {"text": "Practice Python", "category": "learning", "importance": 3, "created_at": "unknown"},
        {"text": "Private reminder", "category": "personal", "importance": 5, "created_at": "unknown"},
    ]


@pytest.mark.parametrize("lookup", [memory_cli.run_search_memories, memory_cli.run_view_memories_by_category])
@pytest.mark.parametrize("value", ["", "   ", " /CANCEL ", EOFError, KeyboardInterrupt])
def test_cancelled_lookup_does_not_search_or_display_memories(monkeypatch, lookup, value):
    memories = sample_memories()
    original = deepcopy(memories)
    output = []
    def read(prompt):
        if value in (EOFError, KeyboardInterrupt):
            raise value()
        return value
    def forbidden(*args):
        pytest.fail("Cancelled lookup must not inspect or change memories.")
    monkeypatch.setattr(memory_cli, "search_memories", forbidden)
    monkeypatch.setattr(memory_cli, "filter_memories_by_category", forbidden)
    monkeypatch.setattr(memory_cli, "save_memories", forbidden)
    result = lookup(memories, read, lambda *parts: output.append(" ".join(map(str, parts))))
    assert result == {"status": "cancelled", "matches": []}
    assert output == ["Memory lookup cancelled."]
    assert memories == original


@pytest.mark.parametrize("lookup,query", [
    (memory_cli.run_search_memories, "  PYTHON  "),
    (memory_cli.run_search_memories, "LEARNING"),
    (memory_cli.run_view_memories_by_category, " Learning "),
])
def test_lookup_matches_without_mutating_or_showing_unrelated_data(lookup, query):
    memories = sample_memories()
    original = deepcopy(memories)
    output = []
    result = lookup(memories, lambda prompt: query, lambda *parts: output.append(" ".join(map(str, parts))))
    assert result == {"status": "completed", "matches": [memories[0]]}
    assert "Practice Python" in "\n".join(output)
    assert "Private reminder" not in "\n".join(output)
    assert memories == original


@pytest.mark.parametrize("lookup,query,status", [
    (memory_cli.run_search_memories, "Not present", "completed"),
    (memory_cli.run_view_memories_by_category, "health", "completed"),
    (memory_cli.run_view_memories_by_category, "invalid", "invalid"),
])
def test_empty_results_and_invalid_category_are_reported(lookup, query, status):
    output = []
    result = lookup([], lambda prompt: query, lambda *parts: output.append(" ".join(map(str, parts))))
    assert result == {"status": status, "matches": []}
    assert output


@pytest.mark.parametrize("option", ["7", "8"])
@pytest.mark.parametrize("value", ["", "/cancel", EOFError, KeyboardInterrupt])
def test_main_cancelled_lookup_preserves_files_and_returns_to_menu(tmp_path, monkeypatch, capsys, option, value):
    directory = tmp_path / "src" / "solitude_kaizen" / "data"
    paths = [directory / "memories.json", directory / "profile.json", directory / "solitude_kaizen.db"]
    data = {"memories": sample_memories(), "session_note": {"unchanged": True}}
    ensure_json_file(paths[0], data)
    ensure_json_file(paths[1], {"user_name": "Test User"})
    initialize_database(paths[2])
    originals = {path: path.read_bytes() for path in paths}
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    def forbidden(*args, **kwargs):
        pytest.fail("Read-only lookup must not call the network.")
    monkeypatch.setattr("requests.sessions.Session.request", forbidden)
    answers = iter([option, value, "27"])
    def read(prompt):
        answer = next(answers)
        if answer in (EOFError, KeyboardInterrupt):
            raise answer()
        return answer
    monkeypatch.setattr("builtins.input", read)
    monkeypatch.chdir(tmp_path)
    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    output = capsys.readouterr().out
    assert "Memory lookup cancelled." in output
    assert "Goodbye!" in output
    assert "Private reminder" not in output
    assert state["memory_data"] == data
    assert state["conversation_history"] == []
    assert all(path.read_bytes() == original for path, original in originals.items())
