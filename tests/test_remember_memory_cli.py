from copy import deepcopy
import runpy

import pytest

from src.solitude_kaizen import json_storage
from src.solitude_kaizen.memory import ensure_json_file, load_memories, validate_importance
from src.solitude_kaizen.memory_cli import run_remember_memory


@pytest.fixture
def saved(tmp_path):
    path = tmp_path / "src" / "solitude_kaizen" / "data" / "memories.json"
    data = {"memories": [], "session_note": {"preserve_unknown_record": True}, "other": "keep"}
    ensure_json_file(path, data)
    return path, data


def read_answers(values):
    values = iter(values)
    def read(prompt):
        value = next(values)
        if value in (EOFError, KeyboardInterrupt):
            raise value()
        return value
    return read


def test_preview_and_confirmation_before_persistence(saved):
    path, data = saved
    before = path.read_bytes()
    original = deepcopy(data)
    shared = data["memories"]
    output = []
    answers = iter(["Use small steps", "project", "4", "yes"])
    def read(prompt):
        assert data == original
        assert path.read_bytes() == before
        if "Type 'yes'" in prompt:
            assert any("New memory preview" in line for line in output)
            assert any("cloud providers" in line for line in output)
        return next(answers)
    item = run_remember_memory(path, data, read, lambda *parts: output.append(" ".join(map(str, parts))))
    assert item["text"] == "Use small steps"
    assert item["category"] == "project"
    assert item["importance"] == 4
    assert data["memories"] is shared
    assert data["memories"] == [item]
    assert data["session_note"] == original["session_note"]
    assert load_memories(path) == data


@pytest.mark.parametrize("stage", range(4))
@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt, "/cancel"])
def test_cancel_at_each_prompt_preserves_data(saved, stage, interruption):
    path, data = saved
    before = path.read_bytes()
    original = deepcopy(data)
    values = ["Keep this", "project", "3", "yes"][:stage] + [interruption]
    assert run_remember_memory(path, data, read_answers(values), lambda *parts: None) is None
    assert data == original
    assert path.read_bytes() == before


@pytest.mark.parametrize("values", [[""], ["   "], ["x" * 1001], ["A note", "test", "2", "no"]])
def test_blank_oversized_or_unconfirmed_memory_not_saved(saved, values):
    path, data = saved
    before = path.read_bytes()
    assert run_remember_memory(path, data, read_answers(values), lambda *parts: None) is None
    assert path.read_bytes() == before
    assert data["memories"] == []


def test_invalid_category_and_unicode_digit_can_be_corrected(saved):
    path, data = saved
    item = run_remember_memory(path, data,
        read_answers(["Keep this", "wrong", "test", "²", "9", "3", " YES "]),
        lambda *parts: None)
    assert item["category"] == "test"
    assert item["importance"] == 3
    assert validate_importance("²") is None


def test_failed_save_keeps_live_list_and_file(saved, monkeypatch):
    path, data = saved
    original = deepcopy(data)
    before = path.read_bytes()
    def fail(*args):
        raise OSError("Test replacement failure")
    monkeypatch.setattr(json_storage.os, "replace", fail)
    item = run_remember_memory(path, data, read_answers(["New", "test", "3", "yes"]), lambda *parts: None)
    assert item is None
    assert data == original
    assert path.read_bytes() == before
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize("confirmation", ["yes", "no"])
def test_main_creation_uses_confirmation_and_preserves_other_fields(saved, tmp_path, monkeypatch, confirmation):
    path, original = saved
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    monkeypatch.setattr("builtins.input", read_answers(["4", "A new memory", "test", "3", confirmation, "27"]))
    monkeypatch.chdir(tmp_path)
    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    result = load_memories(path)
    assert len(result["memories"]) == (1 if confirmation == "yes" else 0)
    assert state["memories"] == result["memories"]
    assert result["session_note"] == original["session_note"]
    assert result["other"] == "keep"
