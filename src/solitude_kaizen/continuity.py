import hashlib
import json
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


BUNDLE_FORMAT_VERSION = 1
ARCHIVE_IDENTITY_PATH = "identity/SK_IDENTITY.md"
ARCHIVE_PROFILE_PATH = "data/profile.json"
ARCHIVE_MEMORIES_PATH = "data/memories.json"
ARCHIVE_DATABASE_PATH = "data/solitude_kaizen.db"
ARCHIVE_MANIFEST_PATH = "manifest.json"

CONTINUITY_FILE_PATHS = (
    ARCHIVE_IDENTITY_PATH,
    ARCHIVE_PROFILE_PATH,
    ARCHIVE_MEMORIES_PATH,
    ARCHIVE_DATABASE_PATH,
)
CONTINUITY_ARCHIVE_PATHS = {
    *CONTINUITY_FILE_PATHS,
    ARCHIVE_MANIFEST_PATH,
}
CONTINUITY_MAX_FILE_SIZES = {
    ARCHIVE_IDENTITY_PATH: 1024 * 1024,
    ARCHIVE_PROFILE_PATH: 1024 * 1024,
    ARCHIVE_MEMORIES_PATH: 32 * 1024 * 1024,
    ARCHIVE_DATABASE_PATH: 256 * 1024 * 1024,
    ARCHIVE_MANIFEST_PATH: 64 * 1024,
}


class ContinuityError(Exception):
    pass


def _sha256(content):
    return hashlib.sha256(content).hexdigest()


def _read_required_file(path, label, maximum_size):
    path = Path(path)

    if not path.is_file():
        raise ContinuityError(f"Required {label} file is missing.")

    if path.stat().st_size > maximum_size:
        raise ContinuityError(
            f"The {label} file is too large for this bundle format."
        )

    content = path.read_bytes()

    if len(content) > maximum_size:
        raise ContinuityError(
            f"The {label} file is too large for this bundle format."
        )

    return content


def _validate_json_bytes(content, label):
    try:
        parsed_content = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContinuityError(
            f"The {label} file is not valid JSON."
        ) from error

    if not isinstance(parsed_content, dict):
        raise ContinuityError(
            f"The {label} file must contain a JSON object."
        )


def _validate_identity_bytes(content):
    try:
        identity_text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContinuityError(
            "The identity file is not valid UTF-8 text."
        ) from error

    if "# Solitude-Kaizen Identity" not in identity_text:
        raise ContinuityError(
            "The identity file does not identify Solitude-Kaizen."
        )


def _validate_database_bytes(content):
    connection = sqlite3.connect(":memory:")

    try:
        connection.deserialize(content)
        result = connection.execute(
            "PRAGMA quick_check"
        ).fetchone()
    except sqlite3.DatabaseError as error:
        raise ContinuityError(
            "The database snapshot is not valid SQLite."
        ) from error
    finally:
        connection.close()

    if result is None or result[0] != "ok":
        raise ContinuityError(
            "The database snapshot did not pass its integrity check."
        )


def _create_database_snapshot(database_path, snapshot_path):
    database_path = Path(database_path)

    if not database_path.is_file():
        raise ContinuityError(
            "Required SQLite database file is missing."
        )

    source = sqlite3.connect(database_path)
    destination = sqlite3.connect(snapshot_path)

    try:
        source.backup(destination)
    except sqlite3.DatabaseError as error:
        raise ContinuityError(
            "The SQLite database could not be backed up."
        ) from error
    finally:
        destination.close()
        source.close()


def _choose_bundle_path(backup_directory, current_time):
    timestamp = current_time.strftime("%Y%m%d-%H%M%S")
    base_name = f"sk-continuity-{timestamp}"
    bundle_path = backup_directory / f"{base_name}.zip"
    counter = 1

    while bundle_path.exists():
        bundle_path = backup_directory / (
            f"{base_name}-{counter}.zip"
        )
        counter += 1

    return bundle_path


def create_continuity_bundle(
    backup_directory,
    database_path,
    profile_path,
    memory_path,
    identity_path,
    current_time=None,
):
    backup_directory = Path(backup_directory)
    backup_directory.mkdir(parents=True, exist_ok=True)

    if current_time is None:
        current_time = datetime.now().astimezone()

    identity_content = _read_required_file(
        identity_path,
        "identity",
        CONTINUITY_MAX_FILE_SIZES[ARCHIVE_IDENTITY_PATH],
    )
    profile_content = _read_required_file(
        profile_path,
        "profile",
        CONTINUITY_MAX_FILE_SIZES[ARCHIVE_PROFILE_PATH],
    )
    memory_content = _read_required_file(
        memory_path,
        "memory",
        CONTINUITY_MAX_FILE_SIZES[ARCHIVE_MEMORIES_PATH],
    )

    _validate_identity_bytes(identity_content)
    _validate_json_bytes(profile_content, "profile")
    _validate_json_bytes(memory_content, "memory")

    bundle_path = _choose_bundle_path(
        backup_directory,
        current_time,
    )

    with tempfile.TemporaryDirectory(
        prefix=".continuity-",
        dir=backup_directory,
    ) as temporary_directory:
        snapshot_path = (
            Path(temporary_directory) / "solitude_kaizen.db"
        )
        _create_database_snapshot(
            database_path,
            snapshot_path,
        )

        if snapshot_path.stat().st_size > (
            CONTINUITY_MAX_FILE_SIZES[ARCHIVE_DATABASE_PATH]
        ):
            raise ContinuityError(
                "The database is too large for this bundle format."
            )

        database_content = snapshot_path.read_bytes()
        _validate_database_bytes(database_content)

        file_contents = {
            ARCHIVE_IDENTITY_PATH: identity_content,
            ARCHIVE_PROFILE_PATH: profile_content,
            ARCHIVE_MEMORIES_PATH: memory_content,
            ARCHIVE_DATABASE_PATH: database_content,
        }
        manifest = {
            "format_version": BUNDLE_FORMAT_VERSION,
            "companion": "Solitude-Kaizen",
            "created_at": current_time.isoformat(
                timespec="seconds"
            ),
            "files": {
                archive_path: {
                    "sha256": _sha256(content),
                    "size": len(content),
                }
                for archive_path, content in file_contents.items()
            },
        }
        manifest_content = json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        temporary_bundle_path = Path(temporary_directory) / (
            bundle_path.name + ".tmp"
        )

        with zipfile.ZipFile(
            temporary_bundle_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as bundle:
            bundle.writestr(
                ARCHIVE_MANIFEST_PATH,
                manifest_content,
            )

            for archive_path, content in file_contents.items():
                bundle.writestr(archive_path, content)

        temporary_bundle_path.replace(bundle_path)

    verification = verify_continuity_bundle(bundle_path)

    if verification["status"] != "valid":
        bundle_path.unlink(missing_ok=True)
        raise ContinuityError(
            "The new continuity bundle failed verification."
        )

    return {
        "bundle_path": str(bundle_path),
        "verification": verification,
    }


def verify_continuity_bundle(bundle_path):
    bundle_path = Path(bundle_path)

    if not bundle_path.is_file():
        return {
            "status": "invalid",
            "created_at": None,
            "file_count": 0,
            "error": "Continuity bundle was not found.",
        }

    try:
        with zipfile.ZipFile(bundle_path, mode="r") as bundle:
            archive_names = bundle.namelist()

            if (
                len(archive_names) != len(set(archive_names))
                or set(archive_names) != CONTINUITY_ARCHIVE_PATHS
            ):
                raise ContinuityError(
                    "The continuity bundle contains unexpected files."
                )

            for archive_name in archive_names:
                archive_info = bundle.getinfo(archive_name)

                if archive_info.file_size > (
                    CONTINUITY_MAX_FILE_SIZES[archive_name]
                ):
                    raise ContinuityError(
                        "A continuity file exceeds its safety limit."
                    )

            manifest = json.loads(
                bundle.read(ARCHIVE_MANIFEST_PATH).decode("utf-8")
            )

            if manifest.get("format_version") != BUNDLE_FORMAT_VERSION:
                raise ContinuityError(
                    "The continuity bundle format is unsupported."
                )

            if manifest.get("companion") != "Solitude-Kaizen":
                raise ContinuityError(
                    "The continuity bundle identity is invalid."
                )

            manifest_files = manifest.get("files")

            if (
                not isinstance(manifest_files, dict)
                or set(manifest_files) != set(CONTINUITY_FILE_PATHS)
            ):
                raise ContinuityError(
                    "The continuity manifest is incomplete."
                )

            verified_contents = {}

            for archive_path in CONTINUITY_FILE_PATHS:
                content = bundle.read(archive_path)
                metadata = manifest_files[archive_path]

                if not isinstance(metadata, dict):
                    raise ContinuityError(
                        "The continuity manifest is invalid."
                    )

                if (
                    metadata.get("size") != len(content)
                    or metadata.get("sha256") != _sha256(content)
                ):
                    raise ContinuityError(
                        "A continuity file failed its integrity check."
                    )

                verified_contents[archive_path] = content

            _validate_json_bytes(
                verified_contents[ARCHIVE_PROFILE_PATH],
                "profile",
            )
            _validate_json_bytes(
                verified_contents[ARCHIVE_MEMORIES_PATH],
                "memory",
            )
            _validate_database_bytes(
                verified_contents[ARCHIVE_DATABASE_PATH]
            )

            _validate_identity_bytes(
                verified_contents[ARCHIVE_IDENTITY_PATH]
            )

            return {
                "status": "valid",
                "created_at": manifest.get("created_at"),
                "file_count": len(CONTINUITY_FILE_PATHS),
                "error": None,
            }
    except (
        ContinuityError,
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
    ) as error:
        return {
            "status": "invalid",
            "created_at": None,
            "file_count": 0,
            "error": str(error) or (
                "Continuity bundle could not be verified."
            ),
        }


def get_latest_continuity_bundle(backup_directory):
    backup_directory = Path(backup_directory)

    if not backup_directory.is_dir():
        return None

    bundles = sorted(
        backup_directory.glob("sk-continuity-*.zip"),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )

    if not bundles:
        return None

    return bundles[0]
