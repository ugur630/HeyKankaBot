import sqlite3
from contextlib import closing
from pathlib import Path


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def connect(self) -> closing[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return closing(connection)

    def create_tables(self) -> None:
        from bot.database.models import TABLE_SCHEMAS

        with self.connect() as connection:
            for schema in TABLE_SCHEMAS:
                connection.execute(schema)
            connection.commit()


def initialize_database(db_path: Path) -> Database:
    database = Database(db_path)
    database.create_tables()
    return database
