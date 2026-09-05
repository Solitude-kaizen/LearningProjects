"""Complete JSON writes before replacing existing local data files."""

import json
import os
import tempfile
from pathlib import Path


def write_json_atomic(path, data):
    """Preserve the old file if serialization, flush, or replacement fails.

    The temporary file stays beside its destination for same-filesystem
    replacement. This does not provide multi-process locking or backups.
    """
    path = Path(path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            # ASCII escaping remains compatible with the existing JSON readers.
            json.dump(data, temporary_file, indent=4, ensure_ascii=True)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
