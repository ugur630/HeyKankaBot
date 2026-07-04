from pathlib import Path
import sqlite3
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from bot.config import DATABASE_PATH
from bot.database.database import initialize_database


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def clear_table(connection: sqlite3.Connection, table_name: str) -> None:
    if table_exists(connection, table_name):
        connection.execute(f"DELETE FROM {table_name}")


def main() -> None:
    initialize_database(DATABASE_PATH)
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        clear_table(connection, "messages")
        print("✓ messages cleared")

        print("✓ conversations cleared")

        clear_table(connection, "memories")
        print("✓ memory cleared")

        clear_table(connection, "cache")
        print("✓ cache cleared")

        clear_table(connection, "tool_calls")

        if table_exists(connection, "sqlite_sequence"):
            connection.execute(
                """
                DELETE FROM sqlite_sequence
                WHERE name IN ('messages', 'memories', 'tool_calls', 'cache')
                """
            )

        connection.commit()
        connection.execute("VACUUM")
        print("✓ VACUUM completed")
    finally:
        connection.close()

    print()
    print("Database reset successful.")


if __name__ == "__main__":
    main()
