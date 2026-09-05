from copy import deepcopy
import json

import pytest

from src.solitude_kaizen import json_storage
from src.solitude_kaizen.memory import ensure_json_file, load_memories, save_memories, save_profile


@pytest.mark.parametrize("save", [save_memories, save_profile])
@pytest.mark.parametrize("failure", ["dump", "fsync", "replace"])
def test_json_save_failure_preserves_original_file(tmp_path, monkeypatch, save, failure):
    path = tmp_path / "data.json"
    old = {"text": "Original", "unrelated": [1, 2]}
    ensure_json_file(path, old)
    before = path.read_bytes()
    new = {"text": "Changed", "unrelated": [1, 2]}
    snapshot = deepcopy(new)

    def fail(*args, **kwargs):
        if failure == "dump":
            args[1].write('{"partly_written":')
        raise OSError("Injected write failure")

    target = json_storage.json if failure == "dump" else json_storage.os
    monkeypatch.setattr(target, failure, fail)
    with pytest.raises(OSError, match="Injected write failure"):
        save(path, new)
    assert path.read_bytes() == before
    assert new == snapshot
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("save", [save_memories, save_profile])
def test_unserializable_data_cannot_truncate_existing_file(tmp_path, save):
    path = tmp_path / "data.json"
    ensure_json_file(path, {"text": "Keep this"})
    before = path.read_bytes()
    with pytest.raises(TypeError):
        save(path, {"text": "New", "unsupported": {1, 2}})
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_save_uses_complete_sibling_before_replacement(tmp_path, monkeypatch):
    path = tmp_path / "memories.json"
    old = {"memories": []}
    ensure_json_file(path, old)
    before = path.read_bytes()
    updated = {"memories": ["Kumusta — 世界"], "session_note": {"version": 99}}
    original_replace = json_storage.os.replace
    replacements = []

    def replace(source, destination):
        assert source.parent == path.parent
        assert destination == path
        assert source != path
        assert json.loads(source.read_text(encoding="utf-8")) == updated
        assert path.read_bytes() == before
        replacements.append(source)
        original_replace(source, destination)

    monkeypatch.setattr(json_storage.os, "replace", replace)
    save_memories(path, updated)
    assert len(replacements) == 1
    assert load_memories(path) == updated
    assert path.read_bytes().isascii()
    assert list(tmp_path.iterdir()) == [path]


def test_failed_initial_creation_leaves_no_partial_file(tmp_path, monkeypatch):
    path = tmp_path / "nested" / "data.json"
    def fail(*args, **kwargs):
        raise OSError("Could not finish writing")
    monkeypatch.setattr(json_storage.os, "fsync", fail)
    with pytest.raises(OSError):
        ensure_json_file(path, {"memories": []})
    assert not path.exists()
    assert list(path.parent.iterdir()) == []


def test_initialization_never_overwrites_existing_file(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    ensure_json_file(path, {"keep": True})
    before = path.read_bytes()
    def unexpected_replace(*args, **kwargs):
        pytest.fail("Existing files must not be initialized again.")
    monkeypatch.setattr(json_storage.os, "replace", unexpected_replace)
    assert ensure_json_file(path, {"keep": False}) is False
    assert path.read_bytes() == before
