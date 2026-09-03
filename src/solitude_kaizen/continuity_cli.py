from dataclasses import dataclass

from .continuity import (
    ContinuityError,
    create_continuity_bundle,
    get_latest_continuity_bundle,
    preview_continuity_restore,
    restore_continuity_bundle,
    verify_continuity_bundle,
)


@dataclass(frozen=True)
class ContinuityPaths:
    backup_directory: str
    database_path: str
    profile_path: str
    memory_path: str
    identity_path: str


def run_create_continuity_backup(
    paths,
    print_function=print,
):
    print_function()
    print_function("Creating a private local continuity backup...")

    try:
        result = create_continuity_bundle(
            paths.backup_directory,
            paths.database_path,
            paths.profile_path,
            paths.memory_path,
            paths.identity_path,
        )
    except ContinuityError as error:
        print_function("The continuity backup could not be created.")
        print_function("Diagnostic:", str(error))

        return {
            "status": "failed",
            "error": str(error),
        }

    print_function("Continuity backup verified successfully.")
    print_function(
        "Files verified:",
        result["verification"]["file_count"],
    )
    print_function("Saved locally at:", result["bundle_path"])
    print_function(
        "Keep this unencrypted backup private. "
        "It does not include .env or credential files."
    )

    return {
        "status": "created",
        **result,
    }


def run_verify_latest_continuity_backup(
    paths,
    print_function=print,
):
    latest_bundle = get_latest_continuity_bundle(
        paths.backup_directory
    )

    print_function()
    print_function("--- Latest Continuity Backup ---")

    if latest_bundle is None:
        print_function("No continuity backup is available yet.")

        return {
            "status": "unavailable",
            "error": None,
        }

    verification = verify_continuity_bundle(latest_bundle)
    print_function("Backup:", latest_bundle)
    print_function("Status:", verification["status"])

    if verification["status"] == "valid":
        print_function("Created:", verification["created_at"])
        print_function(
            "Files verified:",
            verification["file_count"],
        )
    else:
        print_function("Diagnostic:", verification["error"])

    return verification


def run_restore_latest_continuity_backup(
    paths,
    input_function=input,
    print_function=print,
):
    latest_bundle = get_latest_continuity_bundle(
        paths.backup_directory
    )

    print_function()
    print_function("--- Safe Continuity Restore ---")

    if latest_bundle is None:
        print_function("No continuity backup is available yet.")

        return {
            "status": "unavailable",
            "error": None,
        }

    try:
        preview = preview_continuity_restore(
            latest_bundle,
            paths.database_path,
            paths.profile_path,
            paths.memory_path,
            paths.identity_path,
        )
    except ContinuityError as error:
        print_function("The latest backup cannot be restored.")
        print_function("Diagnostic:", str(error))

        return {
            "status": "failed",
            "error": str(error),
        }

    print_function("Verified backup:", preview["bundle_path"])
    print_function("Created:", preview["bundle_created_at"])
    print_function()
    print_function("Proposed file changes:")

    action_labels = {
        "replace": "restore from backup",
        "unchanged": "already matches",
        "blocked": "cannot be safely protected",
    }

    for change in preview["changes"]:
        print_function(
            "-",
            change["archive_path"],
            "->",
            action_labels[change["action"]],
        )
        print_function("  Live file:", change["target_path"])

    if preview["status"] == "blocked":
        print_function()
        print_function("Restore is blocked. Nothing was changed.")

        for blocker in preview["blockers"]:
            print_function("-", blocker)

        print_function(
            "Repair or recover the current files with guidance "
            "before trying again."
        )

        return {
            "status": "blocked",
            "error": preview["blockers"],
            "preview": preview,
        }

    if preview["change_count"] == 0:
        print_function()
        print_function(
            "The current SK files already match this backup."
        )
        print_function("Nothing was changed.")

        return {
            "status": "unchanged",
            "error": None,
            "preview": preview,
        }

    print_function()
    print_function(
        "Before restoring, SK will create and verify an "
        "emergency backup of the current files."
    )
    print_function(
        "If restoration fails, SK will automatically roll back."
    )
    print_function("To continue, type this exact phrase:")
    print_function(preview["confirmation_phrase"])
    confirmation = input_function("Confirmation: ")

    if confirmation != preview["confirmation_phrase"]:
        print_function("Restore canceled. Nothing was changed.")

        return {
            "status": "canceled",
            "error": None,
            "preview": preview,
        }

    try:
        result = restore_continuity_bundle(
            latest_bundle,
            paths.backup_directory,
            paths.database_path,
            paths.profile_path,
            paths.memory_path,
            paths.identity_path,
            confirmation=confirmation,
        )
    except ContinuityError as error:
        print_function("The continuity restore did not complete.")
        print_function("Diagnostic:", str(error))

        return {
            "status": "failed",
            "error": str(error),
            "preview": preview,
        }

    print_function()
    print_function(
        "Continuity restore completed for",
        result["restored_file_count"],
        "file(s).",
    )
    print_function(
        "Emergency backup:",
        result["emergency_bundle_path"],
    )
    print_function(
        "SK will close now so the restored identity and data "
        "can be loaded cleanly on the next start."
    )

    return result
