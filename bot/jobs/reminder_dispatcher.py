from datetime import datetime
import json
import time

from bot.jobs import BaseJob, JobContext
from bot.utils.logger import logger


class ReminderDispatcherJob(BaseJob):
    name = "reminder_dispatcher"

    def __init__(self, context: JobContext) -> None:
        super().__init__(
            context,
            enabled=context.settings.feature_reminder_dispatcher_enabled,
        )

    def should_run(self, current_time: datetime) -> bool:
        del current_time
        return self.enabled

    def run(self) -> None:
        started_at = time.perf_counter()
        logger.info(
            "Reminder dispatcher start: retry_count=%s",
            self.retry_count,
        )
        success = False
        try:
            due_reminders = self.context.reminder_service.get_due_reminders()
            for reminder in due_reminders:
                try:
                    payload = json.dumps(
                        {
                            "status": "due",
                            "message": reminder["message"],
                            "remind_at": reminder["remind_at"],
                            "recurrence": reminder["recurrence"],
                        }
                    )
                    formatted_message = (
                        self.context.response_formatter.format_tool_response(
                            tool_name="reminder",
                            raw_output=payload,
                        )
                    )
                    self.context.telegram_sender.send_text(
                        int(reminder["chat_id"]),
                        formatted_message,
                    )
                    self.context.reminder_service.complete_or_reschedule(
                        reminder,
                    )
                except Exception:
                    logger.exception(
                        "Reminder dispatch failed: reminder_id=%s",
                        reminder.get("id"),
                    )
            success = True
        finally:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.info(
                "Reminder dispatcher finish: success=%s duration_ms=%.2f retry_count=%s",
                success,
                duration_ms,
                self.retry_count,
            )
