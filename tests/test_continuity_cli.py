import json
from pathlib import Path

import pytest

from src.solitude_kaizen.continuity_cli import (
    ContinuityPaths,
    run_create_continuity_backup,
    run_restore_latest_continuity_backup,
    run_verify_latest_continuity_backup,
)
from src.solitude_kaizen.database import initialize_database


def create_continuity_paths(tmp_path):
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
                "current_goal": "Test the CLI boundary",
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

    return ContinuityPaths(
        backup_directory=str(data_directory / "backups"),
        database_path=str(database_path),
        profile_path=str(profile_path),
        memory_path=str(memory_path),
        identity_path=str(identity_path),
    )


def create_output_recorder():
    messages = []

    def record_output(*values):
        messages.append(" ".join(str(value) for value in values))

    return messages, record_output


def test_create_and_verify_backup_flows_report_results(tmp_path):
    paths = create_continuity_paths(tmp_path)
    messages, record_output = create_output_recorder()

    created = run_create_continuity_backup(
        paths,
        print_function=record_output,
    )
    verified = run_verify_latest_continuity_backup(
        paths,
        print_function=record_output,
    )

    assert created["status"] == "created"
    assert verified["status"] == "valid"
    assert "Continuity backup verified successfully." in messages
    assert "Status: valid" in messages


def test_restore_flow_cancels_before_creating_emergency_backup(tmp_path):
    paths = create_continuity_paths(tmp_path)
    created = run_create_continuity_backup(
        paths,
        print_function=lambda *values: None,
    )
    changed_profile = json.dumps({"user_name": "Current User"})
    Path(paths.profile_path).write_text(
        changed_profile,
        encoding="utf-8",
    )
    backup_count = len(
        list(Path(paths.backup_directory).glob("*.zip"))
    )
    messages, record_output = create_output_recorder()

    result = run_restore_latest_continuity_backup(
        paths,
        input_function=lambda prompt: "cancel",
        print_function=record_output,
    )

    assert result["status"] == "canceled"
    assert Path(paths.profile_path).read_text(
        encoding="utf-8"
    ) == changed_profile
    assert len(
        list(Path(paths.backup_directory).glob("*.zip"))
    ) == backup_count
    assert "Restore canceled. Nothing was changed." in messages
    assert Path(created["bundle_path"]).is_file()


def test_restore_flow_returns_restart_signal_after_success(tmp_path):
    paths = create_continuity_paths(tmp_path)
    original_profile = Path(paths.profile_path).read_bytes()
    created = run_create_continuity_backup(
        paths,
        print_function=lambda *values: None,
    )
    Path(paths.profile_path).write_text(
        json.dumps({"user_name": "Current User"}),
        encoding="utf-8",
    )
    confirmation = f"RESTORE {Path(created['bundle_path']).name}"
    messages, record_output = create_output_recorder()

    result = run_restore_latest_continuity_backup(
        paths,
        input_function=lambda prompt: confirmation,
        print_function=record_output,
    )

    assert result["status"] == "restored"
    assert Path(paths.profile_path).read_bytes() == original_profile
    assert Path(result["emergency_bundle_path"]).is_file()
    assert any("SK will close now" in message for message in messages)


def test_restore_flow_does_not_prompt_when_current_state_is_invalid(
    tmp_path,
):
    paths = create_continuity_paths(tmp_path)
    run_create_continuity_backup(
        paths,
        print_function=lambda *values: None,
    )
    Path(paths.memory_path).write_text(
        "not-json",
        encoding="utf-8",
    )
    messages, record_output = create_output_recorder()

    def unexpected_input(prompt):
        pytest.fail("Blocked restore must not request confirmation.")

    result = run_restore_latest_continuity_backup(
        paths,
        input_function=unexpected_input,
        print_function=record_output,
    )

    assert result["status"] == "blocked"
    assert "Restore is blocked. Nothing was changed." in messages
