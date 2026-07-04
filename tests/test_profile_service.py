import tempfile
import unittest
from pathlib import Path

from bot.config import Settings
from bot.database.database import initialize_database
from bot.repositories.user_profile_repository import UserProfileRepository
from bot.services.profile_service import ProfileService


class ProfileServiceTests(unittest.TestCase):
    def test_profiles_are_persisted_outside_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = initialize_database(Path(temp_dir) / "test.db")
            service = ProfileService(
                repository=UserProfileRepository(database),
                settings=Settings(telegram_bot_token="token"),
            )

            service.save_preferences(
                7,
                default_city="Mersin",
                timezone="Europe/Istanbul",
                language="tr",
                morning_notification_enabled=True,
                preferred_reminder_time="08:15",
                favorite_crypto="BTC",
            )

            profile = service.get_profile(7)

            self.assertEqual(profile["default_city"], "Mersin")
            self.assertEqual(profile["preferred_reminder_time"], "08:15")
            self.assertEqual(profile["favorite_crypto"], "BTC")


if __name__ == "__main__":
    unittest.main()
