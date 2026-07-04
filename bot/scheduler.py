from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import time

from bot.config import ensure_runtime_directories, get_settings
from bot.core.response_formatter import ResponseFormatter
from bot.database.database import initialize_database
from bot.jobs import BaseJob, JobContext
from bot.jobs.registry import JobRegistry
from bot.repositories.reminder_repository import ReminderRepository
from bot.repositories.user_profile_repository import UserProfileRepository
from bot.services.profile_service import ProfileService
from bot.services.reminder_parser import ReminderParser
from bot.services.reminder_service import ReminderService
from bot.services.search_service import SearchService
from bot.services.telegram_sender import TelegramSender
from bot.services.weather_service import WeatherService
from bot.utils.logger import logger


@dataclass
class JobScheduler:
    jobs: list[BaseJob]

    def run_pending(self, current_time: datetime | None = None) -> None:
        now = current_time or datetime.now()
        for job in self.jobs:
            if not job.should_run(now):
                continue

            try:
                job.execute(now)
            except Exception:
                logger.exception(
                    "Scheduler caught unhandled job exception: name=%s",
                    getattr(job, "name", "unknown"),
                )
            finally:
                job.mark_ran(now)

    def run_forever(self, poll_interval_seconds: int = 30) -> None:
        while True:
            self.run_pending()
            time.sleep(poll_interval_seconds)


def create_scheduler() -> JobScheduler:
    settings = get_settings()
    ensure_runtime_directories()

    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    database = initialize_database(settings.database_path)
    profile_service = ProfileService(
        repository=UserProfileRepository(database),
        settings=settings,
    )
    reminder_service = ReminderService(
        repository=ReminderRepository(database),
        profile_service=profile_service,
        parser=ReminderParser(),
    )
    context = JobContext(
        settings=settings,
        profile_service=profile_service,
        reminder_service=reminder_service,
        weather_service=WeatherService(
            default_city=settings.default_city,
            timeout_seconds=settings.http_timeout_seconds,
        ),
        search_service=SearchService(
            max_results=settings.search_result_limit,
            timeout_seconds=settings.http_timeout_seconds,
        ),
        response_formatter=ResponseFormatter(),
        telegram_sender=TelegramSender(settings.telegram_bot_token),
    )

    jobs = JobRegistry().build_jobs(context)
    return JobScheduler(jobs=jobs)


def main() -> None:
    logger.info("HeyKankaBot scheduler starting")
    settings = get_settings()
    scheduler = create_scheduler()
    scheduler.run_forever(settings.scheduler_poll_interval_seconds)


if __name__ == "__main__":
    main()
