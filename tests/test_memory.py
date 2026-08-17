from src.solitude_kaizen.memory import (validate_importance, validate_category, normalize_memory,)


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