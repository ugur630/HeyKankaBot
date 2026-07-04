from bot.config import Settings
from bot.repositories.user_profile_repository import UserProfileRepository


class ProfileService:
    def __init__(
        self,
        repository: UserProfileRepository,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.settings = settings

    def get_profile(self, user_id: int) -> dict[str, object]:
        profile = self.repository.get_by_user_id(user_id)
        if profile is not None:
            return profile

        return {
            "user_id": user_id,
            "default_city": self.settings.default_city,
            "timezone": self.settings.default_timezone,
            "language": self.settings.default_language,
            "morning_notification_enabled": True,
            "preferred_reminder_time": self.settings.default_reminder_time,
            "favorite_crypto": "",
        }

    def save_preferences(
        self,
        user_id: int,
        *,
        default_city: str | None = None,
        timezone: str | None = None,
        language: str | None = None,
        morning_notification_enabled: bool | None = None,
        preferred_reminder_time: str | None = None,
        favorite_crypto: str | None = None,
    ) -> dict[str, object]:
        current = self.get_profile(user_id)
        updated = {
            "default_city": (default_city or current["default_city"] or "").strip(),
            "timezone": (timezone or current["timezone"] or "").strip(),
            "language": (language or current["language"] or "").strip(),
            "morning_notification_enabled": (
                current["morning_notification_enabled"]
                if morning_notification_enabled is None
                else morning_notification_enabled
            ),
            "preferred_reminder_time": (
                preferred_reminder_time
                or current["preferred_reminder_time"]
                or self.settings.default_reminder_time
            ).strip(),
            "favorite_crypto": (
                favorite_crypto
                if favorite_crypto is not None
                else str(current["favorite_crypto"] or "")
            ).strip(),
        }
        self.repository.upsert(user_id=user_id, **updated)
        return self.get_profile(user_id)
