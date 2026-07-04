from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import time

from bot.config import Settings
from bot.core.response_formatter import ResponseFormatter
from bot.services.profile_service import ProfileService
from bot.services.reminder_service import ReminderService
from bot.services.search_service import SearchService
from bot.services.telegram_sender import TelegramSender
from bot.services.weather_service import WeatherService
from bot.utils.logger import logger


@dataclass(frozen=True)
class JobContext:
    settings: Settings
    profile_service: ProfileService
    reminder_service: ReminderService
    weather_service: WeatherService
    search_service: SearchService
    response_formatter: ResponseFormatter
    telegram_sender: TelegramSender


class BaseJob(ABC):
    name = "base_job"

    def __init__(
        self,
        context: JobContext,
        *,
        enabled: bool = True,
        notification_time: str | None = None,
    ) -> None:
        self.context = context
        self.enabled = enabled
        self.notification_time = (
            notification_time or context.settings.notification_time
        )
        self.retry_count = 0
        self._last_run_key: str | None = None

    def should_run(self, current_time: datetime) -> bool:
        if not self.enabled:
            return False

        scheduled_hour, scheduled_minute = _parse_notification_time(
            self.notification_time
        )
        scheduled_today = current_time.replace(
            hour=scheduled_hour,
            minute=scheduled_minute,
            second=0,
            microsecond=0,
        )
        if current_time < scheduled_today:
            return False

        run_key = current_time.strftime("%Y-%m-%d")
        return self._last_run_key != run_key

    def execute(self, current_time: datetime | None = None) -> None:
        del current_time
        started_at = time.perf_counter()
        logger.info(
            "Job started: name=%s retry_count=%s",
            self.name,
            self.retry_count,
        )
        success = False
        try:
            self.run()
            success = True
        except Exception:
            logger.exception(
                "Job failed: name=%s retry_count=%s",
                self.name,
                self.retry_count,
            )
        finally:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.info(
                "Job finished: name=%s success=%s retry_count=%s duration_ms=%.2f",
                self.name,
                success,
                self.retry_count,
                duration_ms,
            )

    def mark_ran(self, current_time: datetime) -> None:
        self._last_run_key = current_time.strftime("%Y-%m-%d")

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError


def _parse_notification_time(value: str) -> tuple[int, int]:
    hour_text, minute_text = value.split(":", 1)
    hour = int(hour_text)
    minute = int(minute_text)

    if hour not in range(24) or minute not in range(60):
        raise ValueError(f"Invalid notification time: {value}")

    return hour, minute
