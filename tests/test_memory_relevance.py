from copy import deepcopy

import pytest

from src.solitude_kaizen.memory import (
    build_memory_context,
    rank_memories,
    select_memories_for_context,
)


def make_memory(text, importance=3, created_at="unknown", category="personal"):
    return {
        "text": text,
        "category": category,
        "importance": importance,
        "created_at": created_at,
    }


def test_relevant_memory_displaces_unrelated_high_priority_memories():
    unrelated = [
        make_memory(f"Unrelated reminder {index}", 5, "2026-09-04T12:00:00")
        for index in range(6)
    ]
    relevant = make_memory("Practice Python loops", 1, "2026-08-01T09:00:00")

    selected = select_memories_for_context(
        unrelated + [relevant], query="Help me with Python"
    )

    assert selected == [relevant]


def test_distinct_keyword_overlap_beats_repeated_words_and_priority():
    repeated = make_memory("Python " * 20, 5, "2026-09-04T12:00:00")
    specific = make_memory("Python lists", 1)

    selected = select_memories_for_context(
        [repeated, specific], query="Python Python Python lists"
    )

    assert selected == [specific, repeated]


def test_relevance_ties_keep_importance_recency_and_stable_order():
    old = make_memory("Python old", 5, "2026-08-01T09:00:00")
    low = make_memory("Python low priority", 4, "2026-09-04T12:00:00")
    new_first = make_memory("Python first", 5, "2026-09-01T09:00:00")
    unknown = make_memory("Python unknown date", 5)
    new_second = make_memory("Python second", 5, "2026-09-01T09:00:00")

    selected = select_memories_for_context(
        [old, low, new_first, unknown, new_second], query="Python"
    )

    assert selected == [new_first, new_second, old, unknown, low]


@pytest.mark.parametrize("query,index", [("career", 0), ("AI", 1), ("HR", 2)])
def test_category_and_short_topic_keywords_are_supported(query, index):
    memories = [
        make_memory("Prepare an interview", category="career"),
        make_memory("Explore AI", category="learning"),
        make_memory("Study HR", category="learning"),
    ]

    assert select_memories_for_context(memories, query=query) == [memories[index]]


@pytest.mark.parametrize(
    "query", ["PYTHON?!", "Could you explain Python, please?", "python's"]
)
def test_matching_ignores_case_punctuation_and_common_request_words(query):
    generic = make_memory("Could you explain it to me please", 5)
    relevant = make_memory("Practice Python", 1)

    selected = select_memories_for_context([generic, relevant], query=query)

    assert selected == [relevant]


def test_keywords_match_whole_words_not_substrings():
    javascript = make_memory("Learn JavaScript", 5)
    java = make_memory("Learn Java", 1)

    assert select_memories_for_context([javascript, java], query="Java") == [java]


@pytest.mark.parametrize(
    "query",
    [None, "", "   ", "!?", "could you please tell me about it", "astronomy"],
)
def test_missing_or_unmatched_topic_keeps_existing_ranking(query):
    memories = [
        make_memory("could you please tell me about it", 1),
        make_memory("Save the project", 5, "2026-09-01T09:00:00"),
    ]

    selected = select_memories_for_context(memories, query=query)

    assert selected == rank_memories(memories)


def test_selection_stays_bounded_and_does_not_mutate_memories():
    memories = [
        make_memory(f"Python note {index}", 1 + index % 5)
        for index in range(8)
    ]
    original = deepcopy(memories)

    assert len(select_memories_for_context(memories, query="Python")) == 5
    assert len(select_memories_for_context(memories, 2, query="Python")) == 2
    assert select_memories_for_context(memories, 0, query="Python") == []
    assert memories == original


def test_empty_memories_with_a_topic_remain_empty():
    assert select_memories_for_context([], query="Python") == []
    assert build_memory_context([], query="Python") == (
        "No relevant memories available."
    )


def test_context_uses_query_without_changing_the_memory_format():
    gardening = make_memory("Plan the garden", 5)
    python = make_memory("Practice Python", 1, category="learning")

    context = build_memory_context([gardening, python], 1, query="PYTHON")

    assert context == "- Practice Python (category: learning, importance: 1)"
