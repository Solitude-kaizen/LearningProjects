import runpy

import pytest

from src.solitude_kaizen.database import initialize_database
from src.solitude_kaizen.memory import ensure_json_file


@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt])
@pytest.mark.parametrize("prefix", [[], ["6"], ["6", "1"]])
def test_menu_or_forget_interruption_exits_cleanly_without_saving_note(
    tmp_path, monkeypatch, capsys, interruption, prefix,
):
    directory = tmp_path / "src" / "solitude_kaizen" / "data"
    paths = [directory / "memories.json", directory / "profile.json", directory / "solitude_kaizen.db"]
    data = {"memories": [{"text": "Keep this", "category": "test", "importance": 3,
                          "created_at": "unknown"}]}
    ensure_json_file(paths[0], data)
    ensure_json_file(paths[1], {"user_name": "Test User"})
    initialize_database(paths[2])
    originals = {path: path.read_bytes() for path in paths}
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    def no_network(*args, **kwargs):
        pytest.fail("Exiting cannot call a model or network source.")
    monkeypatch.setattr("requests.sessions.Session.request", no_network)
    answers = iter(prefix)
    def read(prompt):
        try:
            return next(answers)
        except StopIteration:
            raise interruption()
    monkeypatch.setattr("builtins.input", read)
    monkeypatch.chdir(tmp_path)
    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    output = capsys.readouterr().out
    assert "Goodbye! No session note was saved automatically." in output
    assert "Traceback" not in output
    assert state["memory_data"] == data
    assert state["active_session_note"] is None
    assert all(path.read_bytes() == original for path, original in originals.items())
    if prefix:
        assert "Cancelled. Nothing was forgotten." in output


def test_menu_trims_selection_and_explains_unknown_choice(tmp_path, monkeypatch, capsys):
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    answers = iter(["unknown", " 27 "])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.chdir(tmp_path)
    runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    output = capsys.readouterr().out
    assert output.count("Please choose a listed option.") == 1
    assert "Goodbye!" in output
