import tempfile
import unittest
from pathlib import Path

from bot.database.database import initialize_database


class DatabaseIndexTests(unittest.TestCase):
    def test_expected_indexes_are_created(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = initialize_database(Path(temp_dir) / "test.db")

            with database.connect() as connection:
                index_names = {
                    row["name"]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'index'"
                    ).fetchall()
                }

        self.assertIn("idx_messages_user_id_id", index_names)
        self.assertIn("idx_memories_user_id_importance_id", index_names)
        self.assertIn("idx_reminders_status_remind_at", index_names)


if __name__ == "__main__":
    unittest.main()
