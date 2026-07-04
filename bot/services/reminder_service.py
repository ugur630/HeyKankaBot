import json
from datetime import datetime, timedelta
import time

from bot.repositories.reminder_repository import ReminderRepository
from bot.services.profile_service import ProfileService
from bot.services.reminder_parser import ReminderParser
from bot.utils.logger import logger


class ReminderService:
    def __init__(
        self,
        repository: ReminderRepository,
        profile_service: ProfileService,
        parser: ReminderParser,
    ) -> None:
        self.repository = repository
        self.profile_service = profile_service
        self.parser = parser

    def create_reminder(
        self,
        *,
        user_id: int,
        chat_id: int,
        request_text: str,
        now: datetime | None = None,
    ) -> str:
        started_at = time.perf_counter()
        logger.info(
            "Reminder service start: action=create user_id=%s chat_id=%s",
            user_id,
            chat_id,
        )
        success = False
        try:
            current_time = now or datetime.now()
            profile = self.profile_service.get_profile(user_id)
            parsed = self.parser.parse(
                request_text,
                now=current_time,
                default_time=str(profile["preferred_reminder_time"]),
            )
            reminder_id = self.repository.create(
                user_id=user_id,
                chat_id=chat_id,
                message=parsed.message,
                remind_at=parsed.remind_at,
                recurrence=parsed.recurrence,
                timezone=str(profile["timezone"]),
            )
            success = True
            return json.dumps(
                {
                    "status": "scheduled",
                    "reminder_id": reminder_id,
                    "message": parsed.message,
                    "remind_at": parsed.remind_at.isoformat(
                        sep=" ",
                        timespec="minutes",
                    ),
                    "recurrence": parsed.recurrence,
                }
            )
        except ValueError:
            logger.exception("Reminder creation failed")
            return json.dumps(
                {
                    "error": (
                        "Hatirlatma istegini anlayamadim. "
                        "Ornek: 'yarin 09:30'da ilac almayi hatirlat'."
                    ),
                }
            )
        finally:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.info(
                "Reminder service finish: action=create success=%s duration_ms=%.2f",
                success,
                duration_ms,
            )

    def get_due_reminders(
        self,
        now: datetime | None = None,
    ) -> list[dict[str, object]]:
        current_time = now or datetime.now()
        return self.repository.get_due_reminders(current_time)

    def complete_or_reschedule(
        self,
        reminder: dict[str, object],
        *,
        sent_at: datetime | None = None,
    ) -> None:
        current_time = sent_at or datetime.now()
        recurrence = str(reminder.get("recurrence", "none") or "none")
        reminder_id = int(reminder["id"])

        if recurrence == "none":
            self.repository.mark_completed(reminder_id, current_time)
            return

        next_remind_at = self._calculate_next_occurrence(
            remind_at=datetime.fromisoformat(str(reminder["remind_at"])),
            recurrence=recurrence,
        )
        self.repository.reschedule(
            reminder_id,
            next_remind_at=next_remind_at,
            sent_at=current_time,
        )

    def _calculate_next_occurrence(
        self,
        *,
        remind_at: datetime,
        recurrence: str,
    ) -> datetime:
        if recurrence == "daily":
            return remind_at + timedelta(days=1)
        if recurrence == "weekly":
            return remind_at + timedelta(weeks=1)
        if recurrence == "monthly":
            return remind_at + timedelta(days=30)
        if recurrence == "yearly":
            return remind_at + timedelta(days=365)
        return remind_at
