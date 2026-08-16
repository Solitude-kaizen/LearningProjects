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
        if isinstance(memory, dict):
            memory_text = memory["text"]
            memory_category = memory["category"]

            if (
                search_term in memory_text.lower()
                or search_term in memory_category.lower()
            ):
                matches.append(memory)
        else:
            if search_term in memory.lower():
                matches.append(memory)

    return matches

def forget_memory(memories, memory_index):
    if 0 <= memory_index < len(memories):
        return memories.pop(memory_index)

    return None

def format_memory(memory):
    if isinstance(memory, dict):
        importance = memory.get("importance", "not set")
        created_at = memory.get("created_at", "unknown")

        return (
            f"{memory['text']} "
            f"[Category: {memory['category']} "
            f"| Importance: {importance} "
            f"| Created At: {created_at}]"
        )

    return memory

def validate_importance(value):
    if value.isdigit():
        importance = int(value)

        if 1 <= importance <= 5:
            return importance

    return None