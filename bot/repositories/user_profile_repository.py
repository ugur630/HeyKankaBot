from bot.database.database import Database


class UserProfileRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_by_user_id(self, user_id: int) -> dict[str, object] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    user_id,
                    default_city,
                    timezone,
                    language,
                    morning_notification_enabled,
                    preferred_reminder_time,
                    favorite_crypto,
                    created_at,
                    updated_at
                FROM user_profiles
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        if row is None:
            return None

        return {
            "user_id": row["user_id"],
            "default_city": row["default_city"],
            "timezone": row["timezone"],
            "language": row["language"],
            "morning_notification_enabled": bool(
                row["morning_notification_enabled"]
            ),
            "preferred_reminder_time": row["preferred_reminder_time"],
            "favorite_crypto": row["favorite_crypto"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def upsert(
        self,
        user_id: int,
        *,
        default_city: str,
        timezone: str,
        language: str,
        morning_notification_enabled: bool,
        preferred_reminder_time: str,
        favorite_crypto: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO user_profiles (
                    user_id,
                    default_city,
                    timezone,
                    language,
                    morning_notification_enabled,
                    preferred_reminder_time,
                    favorite_crypto
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    default_city = excluded.default_city,
                    timezone = excluded.timezone,
                    language = excluded.language,
                    morning_notification_enabled = excluded.morning_notification_enabled,
                    preferred_reminder_time = excluded.preferred_reminder_time,
                    favorite_crypto = excluded.favorite_crypto,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    default_city,
                    timezone,
                    language,
                    int(morning_notification_enabled),
                    preferred_reminder_time,
                    favorite_crypto,
                ),
            )
            connection.commit()
