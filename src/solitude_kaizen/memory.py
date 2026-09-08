import json
import re
from datetime import datetime
from pathlib import Path

from .json_storage import write_json_atomic


CONTEXT_STOP_WORDS = frozenset(
    "a about an and any are as at be been but by can could did do does "
    "explain for from had has have help how i if in is it its me my of "
    "on or our please should show so some tell than that the their them "
    "there these they this those to us was we were what when where which "
    "who why will with would you your".split()
)


def ensure_json_file(path, default_data):
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if path.exists():
        return False

    write_json_atomic(path, default_data)

    return True

def load_profile(profile_path):
    with open(profile_path, "r") as file:
        profile = json.load(file)

    return profile


def save_profile(profile_path, profile):
    write_json_atomic(profile_path, profile)


def load_memories(memory_path):
    with open(memory_path, "r") as file:
        memory_data = json.load(file)

    return memory_data

def save_memories(memory_path, memory_data):
    write_json_atomic(memory_path, memory_data)

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
        try:
            importance = int(value)
        except ValueError:
            return None

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

    if isinstance(importance, str):
        importance = validate_importance(importance)

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

def sort_memories_by_recency(memories):
    return sorted(
        memories,
        key=lambda memory: (
            memory["created_at"] != "unknown",
            memory["created_at"]
        ),
        reverse=True
    )

def rank_memories(memories):
    return sorted(
        memories,
        key=lambda memory: (
            memory["importance"],
            memory["created_at"] != "unknown",
            memory["created_at"]
        ),
        reverse=True
    )

def _context_keywords(text):
    """Extract simple whole-word keywords without changing stored text."""
    return {
        word
        for word in re.findall(r"[^\W_]+", text.casefold())
        if len(word) > 1
        and not word.isdecimal()
        and word not in CONTEXT_STOP_WORDS
    }


def select_memories_for_context(memories, limit=5, query=None):
    """Use query matches when available, otherwise keep the existing ranking."""
    return [entry["memory"] for entry in explain_memory_selection(memories, limit, query)["selected"]]


def explain_memory_selection(memories, limit=5, query=None):
    """Expose the actual selector's evidence, not a model-generated explanation."""
    ranked_memories = rank_memories(memories)
    query_keywords = _context_keywords(query or "")
    mode = "fallback"
    entries = [{"memory": memory, "matched_keywords": []} for memory in ranked_memories]
    if query_keywords:
        matches = []
        for memory in ranked_memories:
            keywords = _context_keywords(
                f"{memory['text']} {memory['category']}"
            )
            overlap = sorted(query_keywords & keywords)
            if overlap:
                matches.append({"memory": memory, "matched_keywords": overlap})

        if matches:
            # Stable sorting preserves importance and recency for equal scores.
            matches.sort(key=lambda match: len(match["matched_keywords"]), reverse=True)
            entries = matches
            mode = "keyword_match"

    return {
        "mode": mode if memories else "empty",
        "query_keywords": sorted(query_keywords),
        "selected": entries[:limit],
        "total_memories": len(memories),
    }

def build_memory_context(memories, limit=5, query=None):
    selected_memories = select_memories_for_context(
        memories,
        limit=limit,
        query=query,
    )

    if not selected_memories:
        return "No relevant memories available."

    lines = []

    for memory in selected_memories:
        lines.append(
            f"- {memory['text']} "
            f"(category: {memory['category']}, "
            f"importance: {memory['importance']})"
        )

    return "\n".join(lines)
