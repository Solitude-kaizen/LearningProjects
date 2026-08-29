import sqlite3
from pathlib import Path


def initialize_database(database_path):
    database_path = Path(database_path)

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(database_path)
    connection.close()