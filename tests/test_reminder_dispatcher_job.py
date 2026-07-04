import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from bot.config import Settings
from bot.core.response_formatter import ResponseFormatter
from bot.database.database import initialize_database
from bot.jobs import JobContext
from bot.jobs.reminder_dispatcher import ReminderDispatcherJob
from bot.repositories.reminder_repository import ReminderRepository
from bot.repositories.user_profile_repository import UserProfileRepository
from bot.services.profile_service import ProfileService
from bot.services.reminder_parser import ReminderParser
from bot.services.reminder_service import ReminderService
from bot.services.search_service import SearchService
from bot.services.weather_service import WeatherService


class FakeTelegramSender:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    def send_text(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


class FlakyTelegramSender:
    def __init__(self) -> None:
        self.calls = 0
        self.messages: list[tuple[int, str]] = []

    def send_text(self, chat_id: int, text: str) -> None:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary telegram failure")
        self.messages.append((chat_id, text))


class ReminderDispatcherJobTests(unittest.TestCase):
    def test_dispatcher_sends_due_reminder_and_marks_it_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = initialize_database(Path(temp_dir) / "test.db")
            settings = Settings(
                telegram_bot_token="token",
                default_timezone="Europe/Istanbul",
            )
            profile_service = ProfileService(
                repository=UserProfileRepository(database),
                settings=settings,
            )
            reminder_repository = ReminderRepository(database)
            reminder_service = ReminderService(
                repository=reminder_repository,
                profile_service=profile_service,
                parser=ReminderParser(),
            )
            reminder_id = reminder_repository.create(
                user_id=5,
                chat_id=55,
                message="ilac al",
                remind_at=datetime(2026, 7, 4, 8, 0),
                recurrence="none",
                timezone="Europe/Istanbul",
            )
            sender = FakeTelegramSender()
            context = JobContext(
                settings=settings,
                profile_service=profile_service,
                reminder_service=reminder_service,
                weather_service=WeatherService(),
                search_service=SearchService(),
                response_formatter=ResponseFormatter(),
                telegram_sender=sender,
            )

            job = ReminderDispatcherJob(context)
            job.run()

            reminder = reminder_repository.get_by_id(reminder_id)
            self.assertEqual(len(sender.messages), 1)
            self.assertEqual(sender.messages[0][0], 55)
            self.assertIn("Kanka, hatirlatma zamani geldi.", sender.messages[0][1])
            self.assertEqual(reminder["status"], "completed")

    def test_dispatcher_continues_after_single_send_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = initialize_database(Path(temp_dir) / "test.db")
            settings = Settings(telegram_bot_token="token")
            profile_service = ProfileService(
                repository=UserProfileRepository(database),
                settings=settings,
            )
            reminder_repository = ReminderRepository(database)
            reminder_service = ReminderService(
                repository=reminder_repository,
                profile_service=profile_service,
                parser=ReminderParser(),
            )
            reminder_repository.create(
                user_id=5,
                chat_id=55,
                message="ilk not",
                remind_at=datetime(2026, 7, 4, 8, 0),
                recurrence="none",
                timezone="Europe/Istanbul",
            )
            second_id = reminder_repository.create(
                user_id=5,
                chat_id=56,
                message="ikinci not",
                remind_at=datetime(2026, 7, 4, 8, 1),
                recurrence="none",
                timezone="Europe/Istanbul",
            )
            sender = FlakyTelegramSender()
            context = JobContext(
                settings=settings,
                profile_service=profile_service,
                reminder_service=reminder_service,
                weather_service=WeatherService(),
                search_service=SearchService(),
                response_formatter=ResponseFormatter(),
                telegram_sender=sender,
            )

            job = ReminderDispatcherJob(context)
            job.run()

            second = reminder_repository.get_by_id(second_id)
            self.assertEqual(len(sender.messages), 1)
            self.assertEqual(sender.messages[0][0], 56)
            self.assertEqual(second["status"], "completed")


if __name__ == "__main__":
    unittest.main()
