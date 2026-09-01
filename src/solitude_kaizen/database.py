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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS research_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                summary TEXT NOT NULL,
                published_at TEXT,
                discovered_at TEXT NOT NULL,
                UNIQUE (source, external_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS research_collection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL
                    CHECK (
                        status IN ('completed', 'partial', 'failed')
                    ),
                new_item_count INTEGER NOT NULL
                    CHECK (new_item_count >= 0),
                error_summary TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_item_id INTEGER NOT NULL UNIQUE,
                topic TEXT NOT NULL,
                why_it_matters TEXT NOT NULL,
                evidence_summary TEXT NOT NULL,
                evidence_status TEXT NOT NULL
                    CHECK (
                        evidence_status IN ('unreviewed', 'reviewed')
                    ),
                baby_step TEXT NOT NULL,
                reflection_question TEXT NOT NULL,
                improvement_proposal TEXT NOT NULL,
                proposal_status TEXT NOT NULL
                    CHECK (
                        proposal_status IN (
                            'pending', 'approved', 'rejected'
                        )
                    ),
                status TEXT NOT NULL
                    CHECK (status IN ('ready', 'completed')),
                user_reflection TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (research_item_id)
                    REFERENCES research_items (id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS proposal_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learning_lesson_id INTEGER NOT NULL,
                action TEXT NOT NULL
                    CHECK (
                        action IN (
                            'approved', 'rejected', 'postponed'
                        )
                    ),
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (learning_lesson_id)
                    REFERENCES learning_lessons (id)
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


def add_research_item(
    database_path,
    source,
    external_id,
    title,
    url,
    summary,
    published_at,
    discovered_at,
):
    connection = sqlite3.connect(database_path)

    try:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO research_items (
                source,
                external_id,
                title,
                url,
                summary,
                published_at,
                discovered_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source,
                external_id,
                title,
                url,
                summary,
                published_at,
                discovered_at,
            ),
        )
        connection.commit()

        return cursor.rowcount == 1
    finally:
        connection.close()


def get_latest_research_items(database_path, limit=10):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM research_items
            ORDER BY discovered_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()

    return [dict(row) for row in rows]


def record_research_collection_run(
    database_path,
    run_date,
    status,
    new_item_count,
    created_at,
    error_summary=None,
):
    connection = sqlite3.connect(database_path)

    try:
        cursor = connection.execute(
            """
            INSERT INTO research_collection_runs (
                run_date,
                status,
                new_item_count,
                error_summary,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_date,
                status,
                new_item_count,
                error_summary,
                created_at,
            ),
        )
        connection.commit()

        return cursor.lastrowid
    finally:
        connection.close()


def get_research_collection_run_for_date(
    database_path,
    run_date,
):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT *
            FROM research_collection_runs
            WHERE run_date = ?
            """,
            (run_date,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return dict(row)


def get_unstudied_research_items(database_path, limit=50):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT research_items.*
            FROM research_items
            LEFT JOIN learning_lessons
              ON learning_lessons.research_item_id = research_items.id
            WHERE learning_lessons.id IS NULL
            ORDER BY research_items.discovered_at DESC,
                     research_items.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()

    return [dict(row) for row in rows]


def record_learning_lesson(
    database_path,
    research_item_id,
    topic,
    why_it_matters,
    evidence_summary,
    baby_step,
    reflection_question,
    improvement_proposal,
    created_at,
):
    connection = sqlite3.connect(database_path)

    try:
        cursor = connection.execute(
            """
            INSERT INTO learning_lessons (
                research_item_id,
                topic,
                why_it_matters,
                evidence_summary,
                evidence_status,
                baby_step,
                reflection_question,
                improvement_proposal,
                proposal_status,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, 'unreviewed', ?, ?, ?, 'pending',
                    'ready', ?)
            """,
            (
                research_item_id,
                topic,
                why_it_matters,
                evidence_summary,
                baby_step,
                reflection_question,
                improvement_proposal,
                created_at,
            ),
        )
        connection.commit()

        return cursor.lastrowid
    finally:
        connection.close()


def get_learning_lesson_by_id(database_path, lesson_id):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT learning_lessons.*,
                   research_items.source,
                   research_items.url AS source_url,
                   research_items.published_at
            FROM learning_lessons
            JOIN research_items
              ON research_items.id = learning_lessons.research_item_id
            WHERE learning_lessons.id = ?
            """,
            (lesson_id,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return dict(row)


def get_current_learning_lesson(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT learning_lessons.*,
                   research_items.source,
                   research_items.url AS source_url,
                   research_items.published_at
            FROM learning_lessons
            JOIN research_items
              ON research_items.id = learning_lessons.research_item_id
            WHERE learning_lessons.status = 'ready'
            ORDER BY learning_lessons.id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return dict(row)


def get_learning_lesson_for_date(database_path, run_date):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT learning_lessons.*,
                   research_items.source,
                   research_items.url AS source_url,
                   research_items.published_at
            FROM learning_lessons
            JOIN research_items
              ON research_items.id = learning_lessons.research_item_id
            WHERE substr(learning_lessons.created_at, 1, 10) = ?
            ORDER BY learning_lessons.id DESC
            LIMIT 1
            """,
            (run_date,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return dict(row)


def complete_learning_lesson(
    database_path,
    lesson_id,
    user_reflection,
    completed_at,
):
    connection = sqlite3.connect(database_path)

    try:
        cursor = connection.execute(
            """
            UPDATE learning_lessons
            SET status = 'completed',
                evidence_status = 'reviewed',
                user_reflection = ?,
                completed_at = ?
            WHERE id = ?
              AND status = 'ready'
            """,
            (
                user_reflection,
                completed_at,
                lesson_id,
            ),
        )
        connection.commit()

        return cursor.rowcount == 1
    finally:
        connection.close()


def get_learning_progress(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END)
                       AS ready,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
                       AS completed,
                   SUM(CASE WHEN proposal_status = 'pending'
                                 AND status = 'completed'
                            THEN 1 ELSE 0 END)
                       AS pending_proposals
            FROM learning_lessons
            """
        ).fetchone()
    finally:
        connection.close()

    return {
        "total": row["total"],
        "ready": row["ready"] or 0,
        "completed": row["completed"] or 0,
        "pending_proposals": row["pending_proposals"] or 0,
    }


def get_pending_learning_proposals(database_path, limit=20):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT learning_lessons.*,
                   research_items.source,
                   research_items.url AS source_url,
                   (
                       SELECT proposal_reviews.action
                       FROM proposal_reviews
                       WHERE proposal_reviews.learning_lesson_id =
                             learning_lessons.id
                       ORDER BY proposal_reviews.id DESC
                       LIMIT 1
                   ) AS latest_review_action
            FROM learning_lessons
            JOIN research_items
              ON research_items.id = learning_lessons.research_item_id
            WHERE learning_lessons.status = 'completed'
              AND learning_lessons.proposal_status = 'pending'
            ORDER BY learning_lessons.completed_at DESC,
                     learning_lessons.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()

    return [dict(row) for row in rows]


def record_proposal_review(
    database_path,
    learning_lesson_id,
    action,
    reason,
    created_at,
):
    if action not in {"approved", "rejected", "postponed"}:
        raise ValueError("Invalid proposal review action.")

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("BEGIN IMMEDIATE")
        proposal = connection.execute(
            """
            SELECT status, proposal_status
            FROM learning_lessons
            WHERE id = ?
            """,
            (learning_lesson_id,),
        ).fetchone()

        if proposal is None:
            return {
                "status": "not_found",
                "proposal_status": None,
                "review_id": None,
            }

        if proposal["status"] != "completed":
            return {
                "status": "lesson_incomplete",
                "proposal_status": proposal["proposal_status"],
                "review_id": None,
            }

        if proposal["proposal_status"] != "pending":
            return {
                "status": "already_decided",
                "proposal_status": proposal["proposal_status"],
                "review_id": None,
            }

        new_status = "pending"

        if action in {"approved", "rejected"}:
            new_status = action

        connection.execute(
            """
            UPDATE learning_lessons
            SET proposal_status = ?
            WHERE id = ?
            """,
            (new_status, learning_lesson_id),
        )
        cursor = connection.execute(
            """
            INSERT INTO proposal_reviews (
                learning_lesson_id,
                action,
                reason,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                learning_lesson_id,
                action,
                reason,
                created_at,
            ),
        )
        connection.commit()

        return {
            "status": "recorded",
            "proposal_status": new_status,
            "review_id": cursor.lastrowid,
        }
    finally:
        connection.close()


def get_proposal_review_history(database_path, limit=20):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT proposal_reviews.*,
                   learning_lessons.topic,
                   learning_lessons.improvement_proposal,
                   learning_lessons.proposal_status
            FROM proposal_reviews
            JOIN learning_lessons
              ON learning_lessons.id =
                 proposal_reviews.learning_lesson_id
            ORDER BY proposal_reviews.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()

    return [dict(row) for row in rows]
