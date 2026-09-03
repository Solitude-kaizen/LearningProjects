import hashlib
import json
import os
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

import pytest

from src.solitude_kaizen.continuity import (
    ARCHIVE_DATABASE_PATH,
    ARCHIVE_IDENTITY_PATH,
    ARCHIVE_MANIFEST_PATH,
    ARCHIVE_MEMORIES_PATH,
    ARCHIVE_PROFILE_PATH,
    CONTINUITY_ARCHIVE_PATHS,
    ContinuityError,
    create_continuity_bundle,
    get_latest_continuity_bundle,
    preview_continuity_restore,
    restore_continuity_bundle,
    verify_continuity_bundle,
)
from src.solitude_kaizen.database import initialize_database


def create_source_files(tmp_path):
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    database_path = data_directory / "solitude_kaizen.db"
    profile_path = data_directory / "profile.json"
    memory_path = data_directory / "memories.json"
    identity_path = tmp_path / "SK_IDENTITY.md"

    initialize_database(database_path)
    profile_path.write_text(
        json.dumps(
            {
                "user_name": "Test User",
                "current_goal": "Test continuity",
            }
        ),
        encoding="utf-8",
    )
    memory_path.write_text(
        json.dumps({"memories": []}),
        encoding="utf-8",
    )
    identity_path.write_text(
        "# Solitude-Kaizen Identity\n\nIdentity version: 1\n",
        encoding="utf-8",
    )

    return {
        "database": database_path,
        "profile": profile_path,
        "memory": memory_path,
        "identity": identity_path,
        "backups": data_directory / "backups",
    }


def create_test_bundle(tmp_path, current_time=None):
    paths = create_source_files(tmp_path)
    result = create_continuity_bundle(
        paths["backups"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
        current_time=current_time,
    )

    return paths, result


def rewrite_bundle(source_path, destination_path, replacements):
    with zipfile.ZipFile(source_path, mode="r") as source:
        contents = {
            name: source.read(name)
            for name in source.namelist()
        }

    contents.update(replacements)

    with zipfile.ZipFile(
        destination_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as destination:
        for name, content in contents.items():
            destination.writestr(name, content)


def test_continuity_bundle_is_allowlisted_and_verified(tmp_path):
    paths = create_source_files(tmp_path)
    secret_path = tmp_path / ".env"
    secret_path.write_text(
        "OPENAI_API_KEY=must-not-be-backed-up",
        encoding="utf-8",
    )

    result = create_continuity_bundle(
        paths["backups"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
        current_time=datetime(2026, 9, 2, 12, 0, 0),
    )
    bundle_path = result["bundle_path"]

    with zipfile.ZipFile(bundle_path, mode="r") as bundle:
        archive_names = set(bundle.namelist())

    assert archive_names == CONTINUITY_ARCHIVE_PATHS
    assert ".env" not in archive_names
    assert result["verification"] == {
        "status": "valid",
        "created_at": "2026-09-02T12:00:00",
        "file_count": 4,
        "error": None,
    }


def test_invalid_json_is_rejected_before_bundle_creation(tmp_path):
    paths = create_source_files(tmp_path)
    paths["memory"].write_text("not-json", encoding="utf-8")

    with pytest.raises(ContinuityError, match="not valid JSON"):
        create_continuity_bundle(
            paths["backups"],
            paths["database"],
            paths["profile"],
            paths["memory"],
            paths["identity"],
        )

    assert not list(paths["backups"].glob("*.zip"))


def test_wrong_identity_is_rejected_before_bundle_creation(tmp_path):
    paths = create_source_files(tmp_path)
    paths["identity"].write_text(
        "# Another Assistant\n",
        encoding="utf-8",
    )

    with pytest.raises(ContinuityError, match="does not identify"):
        create_continuity_bundle(
            paths["backups"],
            paths["database"],
            paths["profile"],
            paths["memory"],
            paths["identity"],
        )


def test_verification_detects_changed_file_content(tmp_path):
    paths, result = create_test_bundle(tmp_path)
    changed_bundle = paths["backups"] / "changed.zip"
    rewrite_bundle(
        result["bundle_path"],
        changed_bundle,
        {ARCHIVE_PROFILE_PATH: b"{}"},
    )

    verification = verify_continuity_bundle(changed_bundle)

    assert verification["status"] == "invalid"
    assert "integrity check" in verification["error"]


def test_verification_opens_database_in_memory(tmp_path):
    paths, result = create_test_bundle(tmp_path)
    invalid_database = b"not-a-sqlite-database"
    corrupted_bundle = paths["backups"] / "corrupted-db.zip"

    with zipfile.ZipFile(result["bundle_path"], mode="r") as source:
        manifest = json.loads(
            source.read(ARCHIVE_MANIFEST_PATH).decode("utf-8")
        )

    manifest["files"][ARCHIVE_DATABASE_PATH] = {
        "sha256": hashlib.sha256(invalid_database).hexdigest(),
        "size": len(invalid_database),
    }
    rewrite_bundle(
        result["bundle_path"],
        corrupted_bundle,
        {
            ARCHIVE_DATABASE_PATH: invalid_database,
            ARCHIVE_MANIFEST_PATH: json.dumps(manifest).encode(
                "utf-8"
            ),
        },
    )

    verification = verify_continuity_bundle(corrupted_bundle)

    assert verification["status"] == "invalid"
    assert "not valid SQLite" in verification["error"]


def test_latest_continuity_bundle_uses_timestamped_name(tmp_path):
    paths = create_source_files(tmp_path)
    first = create_continuity_bundle(
        paths["backups"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
        current_time=datetime(2026, 9, 1, 12, 0, 0),
    )
    second = create_continuity_bundle(
        paths["backups"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
        current_time=datetime(2026, 9, 2, 12, 0, 0),
    )

    latest = get_latest_continuity_bundle(paths["backups"])

    assert latest.name == "sk-continuity-20260902-120000.zip"
    assert str(latest) == second["bundle_path"]
    assert first["bundle_path"] != second["bundle_path"]
    assert {
        ARCHIVE_IDENTITY_PATH,
        ARCHIVE_PROFILE_PATH,
        ARCHIVE_MEMORIES_PATH,
        ARCHIVE_DATABASE_PATH,
    } < CONTINUITY_ARCHIVE_PATHS


def test_restore_preview_reports_exact_changes_without_writing(tmp_path):
    paths, result = create_test_bundle(tmp_path)
    changed_profile = json.dumps(
        {
            "user_name": "Test User",
            "current_goal": "A newer local goal",
        }
    )
    paths["profile"].write_text(changed_profile, encoding="utf-8")

    preview = preview_continuity_restore(
        result["bundle_path"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
    )

    actions = {
        change["archive_path"]: change["action"]
        for change in preview["changes"]
    }
    assert preview["status"] == "ready"
    assert preview["change_count"] == 1
    assert preview["confirmation_phrase"] == (
        f"RESTORE {Path(result['bundle_path']).name}"
    )
    assert actions[ARCHIVE_PROFILE_PATH] == "replace"
    assert actions[ARCHIVE_MEMORIES_PATH] == "unchanged"
    assert actions[ARCHIVE_IDENTITY_PATH] == "unchanged"
    assert actions[ARCHIVE_DATABASE_PATH] == "unchanged"
    assert paths["profile"].read_text(encoding="utf-8") == changed_profile


def test_restore_requires_exact_confirmation_before_backup_or_write(tmp_path):
    paths, result = create_test_bundle(tmp_path)
    paths["profile"].write_text(
        json.dumps({"user_name": "Current User"}),
        encoding="utf-8",
    )
    bundle_count = len(list(paths["backups"].glob("*.zip")))

    with pytest.raises(ContinuityError, match="confirmation did not match"):
        restore_continuity_bundle(
            result["bundle_path"],
            paths["backups"],
            paths["database"],
            paths["profile"],
            paths["memory"],
            paths["identity"],
            confirmation="yes",
        )

    assert json.loads(paths["profile"].read_text(encoding="utf-8")) == {
        "user_name": "Current User"
    }
    assert len(list(paths["backups"].glob("*.zip"))) == bundle_count


def test_restore_replaces_changed_files_and_keeps_emergency_backup(tmp_path):
    paths, result = create_test_bundle(tmp_path)
    source_profile = paths["profile"].read_bytes()
    paths["profile"].write_text(
        json.dumps({"user_name": "Current User"}),
        encoding="utf-8",
    )
    preview = preview_continuity_restore(
        result["bundle_path"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
    )

    restored = restore_continuity_bundle(
        result["bundle_path"],
        paths["backups"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
        confirmation=preview["confirmation_phrase"],
        current_time=datetime(2026, 9, 3, 12, 0, 0),
    )

    assert restored["status"] == "restored"
    assert restored["restored_file_count"] == 1
    assert paths["profile"].read_bytes() == source_profile
    assert restored["emergency_bundle_path"] != result["bundle_path"]
    assert verify_continuity_bundle(
        restored["emergency_bundle_path"]
    )["status"] == "valid"

    with zipfile.ZipFile(
        restored["emergency_bundle_path"],
        mode="r",
    ) as emergency_bundle:
        emergency_profile = json.loads(
            emergency_bundle.read(ARCHIVE_PROFILE_PATH).decode("utf-8")
        )

    assert emergency_profile == {"user_name": "Current User"}


def test_restore_rolls_back_all_files_when_replacement_fails(tmp_path):
    paths, result = create_test_bundle(tmp_path)
    paths["identity"].write_text(
        "# Solitude-Kaizen Identity\n\nIdentity version: 2\n",
        encoding="utf-8",
    )
    paths["profile"].write_text(
        json.dumps({"user_name": "Current User"}),
        encoding="utf-8",
    )
    connection = sqlite3.connect(paths["database"])

    try:
        connection.execute(
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
                "Keep this current record",
                "test",
                5,
                "2026-09-03T12:00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()
    original_live_contents = {
        key: path.read_bytes()
        for key, path in paths.items()
        if key in {"database", "profile", "memory", "identity"}
    }
    preview = preview_continuity_restore(
        result["bundle_path"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
    )
    replacement_count = 0

    def fail_during_second_replacement(source, destination):
        nonlocal replacement_count
        replacement_count += 1

        if replacement_count == 2:
            raise OSError("simulated replacement failure")

        os.replace(source, destination)

    with pytest.raises(
        ContinuityError,
        match="original files were restored automatically",
    ):
        restore_continuity_bundle(
            result["bundle_path"],
            paths["backups"],
            paths["database"],
            paths["profile"],
            paths["memory"],
            paths["identity"],
            confirmation=preview["confirmation_phrase"],
            current_time=datetime(2026, 9, 3, 12, 0, 0),
            replace_function=fail_during_second_replacement,
        )

    assert replacement_count == 2

    for key, original_content in original_live_contents.items():
        if key == "database":
            continue

        assert paths[key].read_bytes() == original_content

    connection = sqlite3.connect(paths["database"])

    try:
        restored_memory = connection.execute(
            "SELECT text FROM memories"
        ).fetchone()[0]
    finally:
        connection.close()

    assert restored_memory == "Keep this current record"


def test_restore_is_blocked_when_current_state_cannot_be_backed_up(tmp_path):
    paths, result = create_test_bundle(tmp_path)
    paths["memory"].write_text("not-json", encoding="utf-8")

    preview = preview_continuity_restore(
        result["bundle_path"],
        paths["database"],
        paths["profile"],
        paths["memory"],
        paths["identity"],
    )

    assert preview["status"] == "blocked"
    assert preview["change_count"] == 0
    assert "not valid JSON" in preview["blockers"][0]

    with pytest.raises(ContinuityError, match="verified emergency backup"):
        restore_continuity_bundle(
            result["bundle_path"],
            paths["backups"],
            paths["database"],
            paths["profile"],
            paths["memory"],
            paths["identity"],
            confirmation=preview["confirmation_phrase"],
        )
