import runpy

import pytest

from src.solitude_kaizen import memory


@pytest.mark.parametrize("answer,fail_save", [
    ("New goal", False), ("", False), ("New goal", True),
    ("/cancel", False), (EOFError, False), (KeyboardInterrupt, False),
])
def test_goal_changes_only_after_successful_save(tmp_path, monkeypatch, answer, fail_save):
    path = tmp_path / "src" / "solitude_kaizen" / "data" / "profile.json"
    original = {"user_name": "Test", "current_goal": "Original goal", "other": "keep"}
    memory.ensure_json_file(path, original)
    before = path.read_bytes()
    calls = []
    real_save = memory.save_profile
    def save(candidate_path, candidate):
        calls.append(candidate.copy())
        if fail_save:
            raise OSError("Test save failure")
        real_save(candidate_path, candidate)
    monkeypatch.setattr(memory, "save_profile", save)
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    answers = iter(["2", answer, "1", "27"])
    def read(prompt):
        value = next(answers)
        if value in (EOFError, KeyboardInterrupt):
            raise value()
        return value
    monkeypatch.setattr("builtins.input", read)
    monkeypatch.chdir(tmp_path)
    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    successful = answer in ("New goal", "") and not fail_save
    expected = answer if successful else "Original goal"
    assert state["current_goal"] == expected
    assert state["profile"]["current_goal"] == expected
    assert memory.load_profile(path)["current_goal"] == expected
    assert memory.load_profile(path)["other"] == "keep"
    if not successful:
        assert path.read_bytes() == before
    if answer in ("/cancel", EOFError, KeyboardInterrupt):
        assert calls == []
