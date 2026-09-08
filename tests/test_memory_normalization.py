from copy import deepcopy
import runpy

import pytest

from src.solitude_kaizen.memory import ensure_json_file, load_memories, normalize_memory
from src.solitude_kaizen.database import initialize_database


@pytest.mark.parametrize("value,expected", [
    ("²", 3), ("9" * 5000, 3), ("banana", 3), ("", 3),
    ("0", 3), ("6", 3), ("5", 5), ("٢", 2), (2, 2),
])
def test_legacy_importance_normalization_is_safe_and_preserves_source(value, expected):
    record = {
        "text": "Keep this memory", "category": "project",
        "importance": value, "created_at": "2026-09-01T12:00:00",
    }
    original = deepcopy(record)
    normalized = normalize_memory(record)
    assert normalized == {**record, "importance": expected}
    assert record == original


@pytest.mark.parametrize("value", ["²", "9" * 5000])
def test_startup_handles_invalid_legacy_importance(tmp_path, monkeypatch, capsys, value):
    directory = tmp_path / "src" / "solitude_kaizen" / "data"
    memory_path = directory / "memories.json"
    profile_path = directory / "profile.json"
    database_path = directory / "solitude_kaizen.db"
    record = {"text": "Keep this memory", "category": "project", "importance": value, "created_at": "unknown"}
    ensure_json_file(memory_path, {"memories": [record], "unrelated": "preserve"})
    ensure_json_file(profile_path, {"user_name": "Test User"})
    initialize_database(database_path)
    unchanged = {path: path.read_bytes() for path in (profile_path, database_path)}
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    def forbidden(*args, **kwargs):
        pytest.fail("Synthetic startup must not call the network.")
    monkeypatch.setattr("socket.socket.connect", forbidden)
    monkeypatch.setattr("builtins.input", lambda prompt: "27")
    monkeypatch.chdir(tmp_path)
    runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    assert "Goodbye!" in capsys.readouterr().out
    assert load_memories(memory_path) == {"memories": [{**record, "importance": 3}], "unrelated": "preserve"}
    assert all(path.read_bytes() == before for path, before in unchanged.items())
