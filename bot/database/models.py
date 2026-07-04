from bot.database.database import Database

CREATE_MESSAGES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_MEMORIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    importance INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_REMINDERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    remind_at TEXT NOT NULL,
    recurrence TEXT NOT NULL DEFAULT 'none',
    timezone TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    completed_at TEXT,
    last_sent_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_USER_PROFILES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    default_city TEXT NOT NULL DEFAULT '',
    timezone TEXT NOT NULL DEFAULT 'Europe/Istanbul',
    language TEXT NOT NULL DEFAULT 'tr',
    morning_notification_enabled INTEGER NOT NULL DEFAULT 1,
    preferred_reminder_time TEXT NOT NULL DEFAULT '09:00',
    favorite_crypto TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_MESSAGES_USER_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_messages_user_id_id
ON messages (user_id, id)
"""

CREATE_MEMORIES_USER_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_memories_user_id_importance_id
ON memories (user_id, importance, id)
"""

CREATE_REMINDERS_STATUS_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_reminders_status_remind_at
ON reminders (status, remind_at)
"""

TABLE_SCHEMAS = (
    CREATE_MESSAGES_TABLE_SQL,
    CREATE_MEMORIES_TABLE_SQL,
    CREATE_REMINDERS_TABLE_SQL,
    CREATE_USER_PROFILES_TABLE_SQL,
    CREATE_MESSAGES_USER_ID_INDEX_SQL,
    CREATE_MEMORIES_USER_ID_INDEX_SQL,
    CREATE_REMINDERS_STATUS_INDEX_SQL,
)


def save_message(
    database: Database,
    user_id: int,
    role: str,
    content: str,
) -> None:
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO messages (user_id, role, content)
            VALUES (?, ?, ?)
            """,
            (user_id, role, content),
        )
        connection.commit()


def get_last_messages(
    database: Database,
    user_id: int,
    limit: int = 15,
) -> list[dict[str, str]]:
    with database.connect() as connection:
        rows = connection.execute(
            """
            SELECT role, content
            FROM messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [
        {"role": row["role"], "content": row["content"]}
        for row in reversed(rows)
    ]


def clear_history(database: Database, user_id: int) -> None:
    with database.connect() as connection:
        connection.execute(
            "DELETE FROM messages WHERE user_id = ?",
            (user_id,),
        )
        connection.commit()


def delete_old_messages(
    database: Database,
    user_id: int,
    keep: int = 50,
) -> None:
    with database.connect() as connection:
        connection.execute(
            """
            DELETE FROM messages
            WHERE user_id = ?
              AND id NOT IN (
                  SELECT id
                  FROM messages
                  WHERE user_id = ?
                  ORDER BY id DESC
                  LIMIT ?
              )
            """,
            (user_id, user_id, keep),
        )
        connection.commit()


def save_memory(
    database: Database,
    user_id: int,
    key: str,
    value: str,
    importance: int = 1,
) -> None:
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO memories (user_id, key, value, importance)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, key, value, importance),
        )
        connection.commit()


def get_recent_memories(
    database: Database,
    user_id: int,
    limit: int = 5,
) -> list[dict[str, str | int]]:
    with database.connect() as connection:
        rows = connection.execute(
            """
            SELECT id, key, value, importance, created_at
            FROM memories
            WHERE user_id = ?
            ORDER BY importance DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "key": row["key"],
            "value": row["value"],
            "importance": row["importance"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_all_memories(
    database: Database,
    user_id: int,
    limit: int = 250,
) -> list[dict[str, str | int]]:
    with database.connect() as connection:
        rows = connection.execute(
            """
            SELECT id, key, value, importance, created_at
            FROM memories
            WHERE user_id = ?
            ORDER BY importance DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "key": row["key"],
            "value": row["value"],
            "importance": row["importance"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def search_memories(
    database: Database,
    user_id: int,
    query: str,
    limit: int = 5,
) -> list[dict[str, str | int]]:
    normalized = query.strip()
    if not normalized:
        return get_recent_memories(database, user_id, limit=limit)

    tokens = [
        token.lower()
        for token in normalized.replace(".", " ").split()
        if len(token.strip()) >= 3
    ]
    if not tokens:
        tokens = [normalized.lower()]

    like_clauses = " OR ".join(
        "(LOWER(key) LIKE ? OR LOWER(value) LIKE ?)"
        for _ in tokens
    )
    parameters: list[object] = [user_id]
    for token in tokens:
        search_term = f"%{token}%"
        parameters.extend([search_term, search_term])
    parameters.append(limit)

    with database.connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, key, value, importance, created_at
            FROM memories
            WHERE user_id = ?
              AND ({like_clauses})
            ORDER BY importance DESC, id DESC
            LIMIT ?
            """,
            parameters,
        ).fetchall()

    return [
        {
            "id": row["id"],
            "key": row["key"],
            "value": row["value"],
            "importance": row["importance"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def update_memory(
    database: Database,
    user_id: int,
    memory_id: int,
    key: str,
    value: str,
    importance: int,
) -> bool:
    with database.connect() as connection:
        cursor = connection.execute(
            """
            UPDATE memories
            SET key = ?, value = ?, importance = ?
            WHERE id = ? AND user_id = ?
            """,
            (key, value, importance, memory_id, user_id),
        )
        connection.commit()

    return cursor.rowcount > 0


def clear_memories(database: Database, user_id: int) -> None:
    with database.connect() as connection:
        connection.execute(
            "DELETE FROM memories WHERE user_id = ?",
            (user_id,),
        )
        connection.commit()
