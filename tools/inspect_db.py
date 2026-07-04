from pathlib import Path
import sqlite3
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from bot.config import DATABASE_PATH


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


def count_rows(connection: sqlite3.Connection, table_name: str) -> int:
    if not table_exists(connection, table_name):
        return 0

    row = connection.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()
    return int(row[0])


def count_conversations(connection: sqlite3.Connection) -> int:
    if not table_exists(connection, "messages"):
        return 0

    row = connection.execute(
        """
        SELECT COUNT(DISTINCT user_id)
        FROM messages
        """
    ).fetchone()
    return int(row[0])


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def main() -> None:
    if not DATABASE_PATH.exists():
        print("=== Database ===")
        print()
        print("messages        : 0")
        print("conversations   : 0")
        print("memory          : 0")
        print("tool_calls      : 0")
        print()
        print("Database Size : 0 B")
        return

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        messages_count = count_rows(connection, "messages")
        conversations_count = count_conversations(connection)
        memory_count = count_rows(connection, "memories")
        tool_calls_count = count_rows(connection, "tool_calls")
    finally:
        connection.close()

    print("=== Database ===")
    print()
    print(f"messages        : {messages_count}")
    print(f"conversations   : {conversations_count}")
    print(f"memory          : {memory_count}")
    print(f"tool_calls      : {tool_calls_count}")
    print()
    print(f"Database Size : {format_size(DATABASE_PATH.stat().st_size)}")


if __name__ == "__main__":
    main()
