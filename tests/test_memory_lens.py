from copy import deepcopy
import runpy
import random

import pytest

from src.solitude_kaizen import memory_lens_cli
from src.solitude_kaizen.memory import explain_memory_selection, select_memories_for_context, ensure_json_file
from src.solitude_kaizen.database import initialize_database


def memories():
    return [
        {"text": "Python script", "category": "project", "importance": 2, "created_at": "unknown"},
        {"text": "Private reminder", "category": "personal", "importance": 5, "created_at": "unknown"},
    ]


@pytest.mark.parametrize("query,mode,words,index", [
    ("Python SCRIPT!", "keyword_match", ["python", "script"], 0),
    ("project", "keyword_match", ["project"], 0),
    ("unrelated", "fallback", [], 1),
    ("help me", "fallback", [], 1),
    (None, "fallback", [], 1),
])
def test_lens_explains_actual_selection(query, mode, words, index):
    saved = memories()
    original = deepcopy(saved)
    report = explain_memory_selection(saved, limit=1, query=query)
    assert report["mode"] == mode
    assert report["selected"] == [{"memory": saved[index], "matched_keywords": words}]
    assert [item["memory"] for item in report["selected"]] == select_memories_for_context(saved, 1, query)
    assert saved == original


def test_lens_retains_limit_and_stable_ties():
    saved = [dict(memories()[0], text=f"Python script {index}") for index in range(8)]
    report = explain_memory_selection(saved, query="python python")
    assert report["query_keywords"] == ["python"]
    assert [item["memory"] for item in report["selected"]] == saved[:5]
    assert report["total_memories"] == 8


@pytest.mark.parametrize("value,status", [
    ("", "canceled"), (" ", "canceled"), (" /CANCEL ", "canceled"),
    (EOFError, "canceled"), (KeyboardInterrupt, "canceled"), ("x" * 2001, "invalid_query"),
])
def test_lens_invalid_input_never_reads_memories(monkeypatch, value, status):
    def read(prompt):
        if value in (EOFError, KeyboardInterrupt):
            raise value()
        return value
    def forbidden(*args, **kwargs):
        pytest.fail("Must not inspect memories after cancellation or invalid input.")
    monkeypatch.setattr(memory_lens_cli, "explain_memory_selection", forbidden)
    monkeypatch.setattr("builtins.input", read)
    assert memory_lens_cli.run_memory_lens(memories(), print_function=lambda *args: None)["status"] == status


@pytest.mark.parametrize("query", ["python", "unrelated", "/cancel"])
def test_main_lens_is_read_only_and_never_calls_network(tmp_path, monkeypatch, capsys, query):
    directory = tmp_path / "src" / "solitude_kaizen" / "data"
    paths = [directory / "memories.json", directory / "profile.json", directory / "solitude_kaizen.db"]
    data = {"memories": memories()}
    ensure_json_file(paths[0], data)
    ensure_json_file(paths[1], {"user_name": "Test User"})
    initialize_database(paths[2])
    original = {path: path.read_bytes() for path in paths}
    for key in ("SK_RESEARCH_ENABLED", "KAIZEN_DISCOVERY_ENABLED", "SK_CONTINUOUS_LEARNING_ENABLED"):
        monkeypatch.setenv(key, "false")
    def forbidden(*args, **kwargs):
        pytest.fail("Memory Lens must not call a provider or network.")
    monkeypatch.setattr("requests.sessions.Session.request", forbidden)
    monkeypatch.setattr("src.solitude_kaizen.ai_service.generate_response", forbidden)
    answers = iter(["31", query, "27"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.chdir(tmp_path)
    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")
    output = capsys.readouterr().out
    assert "Goodbye!" in output
    assert state["conversation_history"] == []
    assert state["memory_data"] == data
    assert all(path.read_bytes() == before for path, before in original.items())
    if query == "python":
        assert "Shared words: python" in output
        assert "Private reminder" not in output
    elif query == "unrelated":
        assert "These memories may be unrelated" in output
    else:
        assert "Private reminder" not in output


def test_lens_empty_memories_explains_limits():
    output = []
    result = memory_lens_cli.run_memory_lens([], lambda prompt: "python", lambda *parts: output.append(" ".join(map(str, parts))))
    assert result["selection"]["mode"] == "empty"
    assert result["selection"]["selected"] == []
    assert "No saved memories are available." in output
    assert any("not the model's reasoning" in line for line in output)


def test_selection_evidence_agrees_with_independent_generated_cases():
    # Fixed vocabulary makes expected keyword sets independent of the tokenizer.
    rng = random.Random(731)
    vocabulary = ["python", "hiring", "budget", "research", "training"]
    for _ in range(250):
        query_words = set(rng.sample(vocabulary, rng.randrange(4)))
        saved = []
        expected_words = []
        for index in range(rng.randrange(15)):
            words = set(rng.sample(vocabulary, rng.randrange(4)))
            saved.append({
                "text": " ".join(sorted(words)), "category": "personal",
                "importance": rng.randint(1, 5),
                "created_at": rng.choice(["unknown", "2026-08-01", "2026-09-01"]),
            })
            expected_words.append(words & query_words)
        indices = list(range(len(saved)))
        matching = [index for index in indices if expected_words[index]]
        expected = sorted(matching or indices, key=lambda index: (
            len(expected_words[index]), saved[index]["importance"],
            saved[index]["created_at"] != "unknown", saved[index]["created_at"],
        ), reverse=True)[:5]
        report = explain_memory_selection(saved, query=" ".join(sorted(query_words)))
        assert [entry["memory"] for entry in report["selected"]] == [saved[index] for index in expected]
        assert [entry["matched_keywords"] for entry in report["selected"]] == [sorted(expected_words[index]) for index in expected]
        assert report["mode"] == ("empty" if not saved else "keyword_match" if matching else "fallback")
