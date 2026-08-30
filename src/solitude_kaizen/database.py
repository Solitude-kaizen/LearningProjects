import sqlite3
from pathlib import Path


def initialize_database(database_path):
    database_path = Path(database_path)

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(database_path)

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                category TEXT NOT NULL,
                importance INTEGER NOT NULL
                    CHECK (importance BETWEEN 1 AND 5),
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS kaizen_discoveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL
                    CHECK (status IN ('completed', 'failed')),
                report TEXT NOT NULL,
                provider TEXT NOT NULL,
                error_kind TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def add_memory(
    database_path,
    text,
    category,
    importance,
    created_at,
):
    connection = sqlite3.connect(database_path)

    try:
        cursor = connection.execute(
            """
            INSERT INTO memories (
                text,
                category,
                importance,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                text,
                category,
                importance,
                created_at,
            ),
        )
        connection.commit()

        return cursor.lastrowid
    finally:
        connection.close()


def record_kaizen_discovery(
    database_path,
    run_date,
    status,
    report,
    provider,
    created_at,
    error_kind=None,
):
    connection = sqlite3.connect(database_path)

    try:
        cursor = connection.execute(
            """
            INSERT INTO kaizen_discoveries (
                run_date,
                status,
                report,
                provider,
                error_kind,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_date,
                status,
                report,
                provider,
                error_kind,
                created_at,
            ),
        )
        connection.commit()

        return cursor.lastrowid
    finally:
        connection.close()


def get_kaizen_discovery_for_date(database_path, run_date):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT *
            FROM kaizen_discoveries
            WHERE run_date = ?
            """,
            (run_date,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return dict(row)


def get_latest_kaizen_discovery(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT *
            FROM kaizen_discoveries
            ORDER BY run_date DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return dict(row)
