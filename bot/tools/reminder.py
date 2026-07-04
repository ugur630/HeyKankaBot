from bot.services.reminder_service import ReminderService


def create_reminder(
    query: str,
    user_id: int,
    chat_id: int,
    reminder_service: ReminderService,
) -> str:
    return reminder_service.create_reminder(
        user_id=user_id,
        chat_id=chat_id,
        request_text=query,
    )
