from src.solitude_kaizen.database import initialize_database


def test_initialize_database_creates_database(tmp_path):
    database_path = tmp_path / "data" / "solitude_kaizen.db"

    initialize_database(database_path)

    assert database_path.exists()
