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
)


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