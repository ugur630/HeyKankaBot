import tempfile
import unittest
from pathlib import Path

from bot.database.database import initialize_database
from bot.services.memory_service import MAX_MEMORY_VALUE_LENGTH, MemoryService


class MemoryValueLengthLimitTests(unittest.TestCase):
    def test_remember_truncates_oversized_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = initialize_database(Path(temp_dir) / "test.db")
            memory_service = MemoryService(database=database)

            memory_service.remember(
                user_id=1,
                key="note",
                value="x" * 5000,
            )

            stored = memory_service.recall(user_id=1)

        self.assertEqual(len(stored[0]["value"]), MAX_MEMORY_VALUE_LENGTH)

    def test_remember_leaves_short_values_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = initialize_database(Path(temp_dir) / "test.db")
            memory_service = MemoryService(database=database)

            memory_service.remember(
                user_id=1,
                key="name",
                value="Ugur",
            )

            stored = memory_service.recall(user_id=1)

        self.assertEqual(stored[0]["value"], "Ugur")


if __name__ == "__main__":
    unittest.main()
