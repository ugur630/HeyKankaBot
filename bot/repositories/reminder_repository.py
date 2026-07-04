from datetime import datetime

from bot.database.database import Database


class ReminderRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        *,
        user_id: int,
        chat_id: int,
        message: str,
        remind_at: datetime,
        recurrence: str,
        timezone: str,
        status: str = "pending",
    ) -> int:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reminders (
                    user_id,
                    chat_id,
                    message,
                    remind_at,
                    recurrence,
                    timezone,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    chat_id,
                    message,
                    remind_at.isoformat(sep=" ", timespec="minutes"),
                    recurrence,
                    timezone,
                    status,
                ),
            )
            connection.commit()

        return int(cursor.lastrowid)

    def get_due_reminders(
        self,
        now: datetime,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    chat_id,
                    message,
                    remind_at,
                    recurrence,
                    timezone,
                    status,
                    created_at,
                    completed_at,
                    last_sent_at
                FROM reminders
                WHERE status = 'pending'
                  AND remind_at <= ?
                ORDER BY remind_at ASC, id ASC
                LIMIT ?
                """,
                (
                    now.isoformat(sep=" ", timespec="minutes"),
                    limit,
                ),
            ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def mark_completed(
        self,
        reminder_id: int,
        completed_at: datetime,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE reminders
                SET status = 'completed',
                    completed_at = ?,
                    last_sent_at = ?
                WHERE id = ?
                """,
                (
                    completed_at.isoformat(sep=" ", timespec="minutes"),
                    completed_at.isoformat(sep=" ", timespec="minutes"),
                    reminder_id,
                ),
            )
            connection.commit()

    def reschedule(
        self,
        reminder_id: int,
        *,
        next_remind_at: datetime,
        sent_at: datetime,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE reminders
                SET remind_at = ?,
                    last_sent_at = ?,
                    status = 'pending'
                WHERE id = ?
                """,
                (
                    next_remind_at.isoformat(sep=" ", timespec="minutes"),
                    sent_at.isoformat(sep=" ", timespec="minutes"),
                    reminder_id,
                ),
            )
            connection.commit()

    def get_by_id(self, reminder_id: int) -> dict[str, object] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    chat_id,
                    message,
                    remind_at,
                    recurrence,
                    timezone,
                    status,
                    created_at,
                    completed_at,
                    last_sent_at
                FROM reminders
                WHERE id = ?
                """,
                (reminder_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_dict(row)

    def _row_to_dict(self, row) -> dict[str, object]:
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "chat_id": row["chat_id"],
            "message": row["message"],
            "remind_at": row["remind_at"],
            "recurrence": row["recurrence"],
            "timezone": row["timezone"],
            "status": row["status"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
            "last_sent_at": row["last_sent_at"],
        }
