import json
from datetime import datetime

def load_profile(profile_path):
    with open(profile_path, "r") as file:
        profile = json.load(file)

    return profile


def save_profile(profile_path, profile):
    with open(profile_path, "w") as file:
        json.dump(profile, file, indent=4)


def load_memories(memory_path):
    with open(memory_path, "r") as file:
        memory_data = json.load(file)

    return memory_data

def save_memories(memory_path, memory_data):
    with open(memory_path, "w") as file:
        json.dump(memory_data, file, indent=4)

def create_memory(text, category, importance):
    created_at = datetime.now().isoformat(timespec="seconds")

    return {
        "text": text,
        "category": category,
        "importance": importance,
        "created_at": created_at
    }

def search_memories(memories, search_term):
    matches = []

    search_term = search_term.lower()

    for memory in memories:
        memory_text = memory["text"]
        memory_category = memory["category"]

        if (
            search_term in memory_text.lower()
            or search_term in memory_category.lower()
        ):
            matches.append(memory)

    return matches

def forget_memory(memories, memory_index):
    if 0 <= memory_index < len(memories):
        return memories.pop(memory_index)

    return None

def format_memory(memory):
    importance = memory.get("importance", "not set")
    created_at = memory.get("created_at", "unknown")

    return (
        f"{memory['text']} "
        f"[Category: {memory['category']} "
        f"| Importance: {importance} "
        f"| Created At: {created_at}]"
    )

def validate_importance(value):
    if value.isdigit():
        importance = int(value)

        if 1 <= importance <= 5:
            return importance

    return None

def validate_category(value):
    valid_categories = [
        "learning",
        "career",
        "health",
        "project",
        "personal",
        "test"
    ]

    category = value.strip().lower()

    if category in valid_categories:
        return category

    return None

def normalize_memory(memory):
    if not isinstance(memory, dict):
        return {
            "text": memory,
            "category": "personal",
            "importance": 3,
            "created_at": "unknown"
        }

    text = memory.get("text", "")

    category = memory.get("category", "personal")
    category = category.strip().lower()

    importance = memory.get("importance", 3)

    if isinstance(importance, str) and importance.isdigit():
        importance = int(importance)

    if not isinstance(importance, int) or not 1 <= importance <= 5:
        importance = 3

    created_at = memory.get("created_at", "unknown")

    return {
        "text": text,
        "category": category,
        "importance": importance,
        "created_at": created_at
    }

def filter_memories_by_category(memories, category):
    category = category.strip().lower()

    matches = []

    for memory in memories:
        if memory["category"] == category:
            matches.append(memory)

    return matches

def sort_memories_by_importance(memories):
    return sorted(
        memories,
        key=lambda memory: memory["importance"],
        reverse=True
    )