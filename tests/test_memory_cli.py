from copy import deepcopy
import runpy

import pytest

from src.solitude_kaizen import memory, memory_cli


@pytest.fixture
def saved_memories(tmp_path):
    memory_path = (
        tmp_path / "src" / "solitude_kaizen" / "data" / "memories.json"
    )
    memory_data = {
        "memories": [
            memory.create_memory("Keep the first", "test", 3),
            memory.create_memory("Selected memory", "test", 4),
            memory.create_memory("Keep the last", "test", 2),
        ],
        "test_metadata": "Preserve unrelated fields",
    }
    memory.ensure_json_file(memory_path, memory_data)
    return memory_path, memory_data


def create_output_recorder():
    messages = []

    def record_output(*parts):
        messages.append(" ".join(str(part) for part in parts))

    return messages, record_output


@pytest.fixture
def forbid_memory_changes(monkeypatch):
    def unexpected_change(*args, **kwargs):
        pytest.fail("An unconfirmed selection must not delete or save.")

    monkeypatch.setattr(memory_cli, "forget_memory", unexpected_change)
    monkeypatch.setattr(memory_cli, "save_memories", unexpected_change)


@pytest.mark.parametrize("stage", ["selection", "confirmation"])
@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt])
def test_interrupted_forgetting_preserves_list_and_bytes(
    saved_memories, forbid_memory_changes, stage, interruption,
):
    memory_path, memory_data = saved_memories
    original = deepcopy(memory_data)
    original_bytes = memory_path.read_bytes()
    prompts = []
    messages, record_output = create_output_recorder()

    def read(prompt):
        prompts.append(prompt)
        if stage == "selection" or len(prompts) == 2:
            raise interruption()
        return "2"

    assert memory_cli.run_forget_memory(memory_path, memory_data, read, record_output) is None
    assert memory_data == original
    assert memory_path.read_bytes() == original_bytes
    assert "Cancelled. Nothing was forgotten." in messages


def test_explicit_cancel_at_memory_selection_keeps_data(saved_memories, forbid_memory_changes):
    memory_path, memory_data = saved_memories
    original = deepcopy(memory_data)
    original_bytes = memory_path.read_bytes()
    messages, record_output = create_output_recorder()
    memory_cli.run_forget_memory(memory_path, memory_data, lambda prompt: " /CANCEL ", record_output)
    assert memory_data == original
    assert memory_path.read_bytes() == original_bytes
    assert "Cancelled. Nothing was forgotten." in messages


@pytest.mark.parametrize("confirmation", ["yes", "YES", " yes "])
def test_forget_failed_save_keeps_shared_memory_state(saved_memories, monkeypatch, confirmation):
    memory_path, memory_data = saved_memories
    original = deepcopy(memory_data)
    original_bytes = memory_path.read_bytes()
    shared_memories = memory_data["memories"]
    messages, output = create_output_recorder()

    def fail_save(path, candidate):
        assert memory_data == original
        assert candidate["memories"] != shared_memories
        raise OSError("Failed test save")

    monkeypatch.setattr(memory_cli, "save_memories", fail_save)
    answers = iter(["2", confirmation])
    assert memory_cli.run_forget_memory(
        memory_path, memory_data, lambda prompt: next(answers), output,
    ) is None
    assert memory_data == original
    assert memory_data["memories"] is shared_memories
    assert memory_path.read_bytes() == original_bytes
    assert "Could not save the change. Nothing was forgotten." in messages


@pytest.mark.parametrize("confirmation", ["yes", "YES", " yes "])
def test_forget_previews_then_saves_only_confirmed_selection(
    saved_memories,
    monkeypatch,
    confirmation,
):
    memory_path, memory_data = saved_memories
    original = deepcopy(memory_data)
    original_bytes = memory_path.read_bytes()
    original_list = memory_data["memories"]
    messages, record_output = create_output_recorder()
    prompts = []
    saved = []

    def read_input(prompt):
        prompts.append(prompt)
        assert memory_data == original
        assert memory_path.read_bytes() == original_bytes
        assert saved == []
        if len(prompts) == 1:
            return "2"
        assert len(prompts) == 2
        assert "Type 'yes'" in prompt
        assert messages[-2] == "You are about to forget:"
        assert messages[-1] == (
            "- " + memory.format_memory(original["memories"][1])
        )
        return confirmation

    def record_save(path, data):
        assert path == memory_path
        saved.append(deepcopy(data))
        memory.save_memories(path, data)

    monkeypatch.setattr(memory_cli, "save_memories", record_save)
    result = memory_cli.run_forget_memory(
        memory_path, memory_data, read_input, record_output
    )

    expected = deepcopy(original)
    selected = expected["memories"].pop(1)
    assert result == selected
    assert len(prompts) == 2
    assert memory_data["memories"] is original_list
    assert memory_data == expected
    assert memory.load_memories(memory_path) == expected
    assert saved == [expected]
    assert any(message.startswith("I forgot:") for message in messages)


@pytest.mark.parametrize("confirmation", ["no", "", "y", "yes please"])
def test_forget_cancel_preserves_list_and_file_without_saving(
    saved_memories,
    forbid_memory_changes,
    confirmation,
):
    memory_path, memory_data = saved_memories
    original = deepcopy(memory_data)
    original_bytes = memory_path.read_bytes()
    answers = iter(["2", confirmation])
    messages, record_output = create_output_recorder()

    result = memory_cli.run_forget_memory(
        memory_path,
        memory_data,
        input_function=lambda prompt: next(answers),
        print_function=record_output,
    )

    assert result is None
    assert memory_data == original
    assert memory_path.read_bytes() == original_bytes
    assert "You are about to forget:" in messages
    assert "Cancelled. Nothing was forgotten." in messages
    assert not any(message.startswith("I forgot:") for message in messages)


@pytest.mark.parametrize("selection", ["", "banana", "0", "-1", "4", "1.5", "²"])
def test_invalid_selection_does_not_confirm_delete_or_save(
    saved_memories,
    forbid_memory_changes,
    selection,
):
    memory_path, memory_data = saved_memories
    original = deepcopy(memory_data)
    original_bytes = memory_path.read_bytes()
    prompts = []
    messages, record_output = create_output_recorder()

    def read_input(prompt):
        prompts.append(prompt)
        assert len(prompts) == 1
        return selection

    result = memory_cli.run_forget_memory(
        memory_path, memory_data, read_input, record_output
    )

    assert result is None
    assert len(prompts) == 1
    assert memory_data == original
    assert memory_path.read_bytes() == original_bytes
    assert "You are about to forget:" not in messages
    assert messages[-1] in (
        "Please enter a valid number.",
        "That memory number does not exist.",
    )


def test_empty_memories_do_not_prompt_or_save(tmp_path, forbid_memory_changes):
    memory_path = tmp_path / "empty.json"
    memory_data = {"memories": []}
    memory.ensure_json_file(memory_path, memory_data)
    original_bytes = memory_path.read_bytes()
    messages, record_output = create_output_recorder()

    def unexpected_input(prompt):
        pytest.fail("There is no memory to select or confirm.")

    result = memory_cli.run_forget_memory(
        memory_path, memory_data, unexpected_input, record_output
    )

    assert result is None
    assert memory_data == {"memories": []}
    assert memory_path.read_bytes() == original_bytes
    assert messages == ["I do not have any memories to forget."]


@pytest.mark.parametrize("confirmation", ["yes", "no"])
def test_main_routes_forgetting_through_confirmation_and_persistence(
    saved_memories,
    tmp_path,
    monkeypatch,
    capsys,
    confirmation,
):
    memory_path, memory_data = saved_memories
    original = deepcopy(memory_data)
    original_bytes = memory_path.read_bytes()
    expected = deepcopy(original)
    if confirmation == "yes":
        expected["memories"].pop(1)

    saved = []
    save_function = memory.save_memories

    def record_save(path, data):
        saved.append(deepcopy(data))
        save_function(path, data)

    monkeypatch.setattr(memory, "save_memories", record_save)
    monkeypatch.setattr(memory_cli, "save_memories", record_save)
    monkeypatch.setenv("SK_RESEARCH_ENABLED", "false")
    monkeypatch.setenv("KAIZEN_DISCOVERY_ENABLED", "false")
    monkeypatch.setenv("SK_CONTINUOUS_LEARNING_ENABLED", "false")
    answers = iter(["6", "2", confirmation, "5", "27"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.chdir(tmp_path)

    state = runpy.run_module("src.solitude_kaizen.main", run_name="__main__")

    output = capsys.readouterr().out
    assert "You are about to forget:" in output
    assert "Goodbye!" in output
    assert state["memories"] == expected["memories"]
    assert state["memory_data"] == expected
    assert memory.load_memories(memory_path) == expected
    # Startup already normalizes and saves memories; the action must only
    # add a second write when the user explicitly confirms deletion.
    if confirmation == "yes":
        assert "I forgot:" in output
        assert saved == [original, expected]
    else:
        assert "Cancelled. Nothing was forgotten." in output
        assert "I forgot:" not in output
        assert saved == [original]
        assert memory_path.read_bytes() == original_bytes
