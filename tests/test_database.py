import sqlite3

from src.solitude_kaizen.database import (
    add_memory,
    initialize_database,
)


def test_initialize_database_creates_database(tmp_path):
    database_path = tmp_path / "data" / "solitude_kaizen.db"

    initialize_database(database_path)

    assert database_path.exists()


def test_initialize_database_creates_memories_table(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"

    initialize_database(database_path)

    connection = sqlite3.connect(database_path)

    try:
        columns = connection.execute(
            "PRAGMA table_info(memories)"
        ).fetchall()
    finally:
        connection.close()

    column_names = [column[1] for column in columns]

    assert column_names == [
        "id",
        "text",
        "category",
        "importance",
        "created_at",
    ]


def test_initialize_database_creates_v2_tables(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"

    initialize_database(database_path)

    connection = sqlite3.connect(database_path)

    try:
        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (
                  'learning_lessons',
                  'proposal_reviews',
                  'research_items',
                  'research_collection_runs'
              )
            ORDER BY name
            """
        ).fetchall()
    finally:
        connection.close()

    assert table_rows == [
        ("learning_lessons",),
        ("proposal_reviews",),
        ("research_collection_runs",),
        ("research_items",),
    ]


def test_add_memory_inserts_memory_and_returns_id(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    initialize_database(database_path)

    memory_id = add_memory(
        database_path,
        "I'm learning parameterized SQL.",
        "learning",
        4,
        "2026-08-30T20:00:00",
    )

    connection = sqlite3.connect(database_path)

    try:
        stored_memory = connection.execute(
            """
            SELECT id, text, category, importance, created_at
            FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        ).fetchone()
    finally:
        connection.close()

    assert stored_memory == (
        memory_id,
        "I'm learning parameterized SQL.",
        "learning",
        4,
        "2026-08-30T20:00:00",
    )
