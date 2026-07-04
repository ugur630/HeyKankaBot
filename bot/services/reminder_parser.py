from dataclasses import dataclass
from datetime import datetime, timedelta
import re


TURKISH_CHAR_MAP = str.maketrans(
    {
        "\u00e7": "c",
        "\u011f": "g",
        "\u0131": "i",
        "\u00f6": "o",
        "\u015f": "s",
        "\u00fc": "u",
    }
)

REMINDER_KEYWORDS = (
    "hatirlat",
    "remind",
)


@dataclass(frozen=True)
class ReminderParseResult:
    message: str
    remind_at: datetime
    recurrence: str


class ReminderParser:
    def parse(
        self,
        text: str,
        *,
        now: datetime,
        default_time: str,
    ) -> ReminderParseResult:
        normalized = self._normalize(text)
        recurrence = self._extract_recurrence(normalized)
        remind_date = self._extract_date(normalized, now)
        remind_time = self._extract_time(normalized) or default_time
        remind_at = self._combine_datetime(remind_date, remind_time)
        if recurrence == "none" and remind_at <= now:
            remind_at = remind_at + timedelta(days=1)
        if recurrence != "none":
            while remind_at <= now:
                remind_at = self._advance_recurrence(
                    remind_at=remind_at,
                    recurrence=recurrence,
                )

        message = self._extract_message(text, normalized)
        if not message:
            raise ValueError("Reminder message is empty.")

        return ReminderParseResult(
            message=message,
            remind_at=remind_at,
            recurrence=recurrence,
        )

    def _extract_date(self, normalized: str, now: datetime) -> datetime.date:
        explicit_date = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", normalized)
        if explicit_date:
            year, month, day = (
                int(explicit_date.group(1)),
                int(explicit_date.group(2)),
                int(explicit_date.group(3)),
            )
            return datetime(year, month, day).date()

        if "yarin" in normalized:
            return (now + timedelta(days=1)).date()

        return now.date()

    def _extract_time(self, normalized: str) -> str:
        explicit_time = re.search(
            r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b",
            normalized,
        )
        if explicit_time:
            return f"{int(explicit_time.group(1)):02d}:{explicit_time.group(2)}"
        return ""

    def _extract_recurrence(self, normalized: str) -> str:
        recurrence_keywords = {
            "daily": ("her gun", "gunluk", "daily"),
            "weekly": ("her hafta", "haftalik", "weekly"),
            "monthly": ("her ay", "aylik", "monthly"),
            "yearly": ("her yil", "yillik", "yearly"),
        }
        for recurrence, keywords in recurrence_keywords.items():
            if any(keyword in normalized for keyword in keywords):
                return recurrence
        return "none"

    def _extract_message(self, original: str, normalized: str) -> str:
        candidate = original.strip()
        candidate = re.sub(
            r"(?i)\b(bana|beni|lutfen|lütfen)\b",
            " ",
            candidate,
        )
        candidate = re.sub(
            r"(?i)\b(hatirlat|hatırlat|hatirlat|remind me)\b",
            " ",
            candidate,
        )
        candidate = re.sub(
            r"(?i)\b(yarin|yarın|bugun|bugün)\b",
            " ",
            candidate,
        )
        candidate = re.sub(
            r"\b\d{4}-\d{2}-\d{2}\b",
            " ",
            candidate,
        )
        candidate = re.sub(
            r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b",
            " ",
            candidate,
        )
        candidate = re.sub(
            r"(?i)(['’](de|da|te|ta))|\b(saat|her gun|her gün|gunluk|haftalik|aylik|yillik|her hafta|her ay|her yil)\b",
            " ",
            candidate,
        )
        candidate = " ".join(candidate.replace("  ", " ").split())
        candidate = candidate.strip(" -,.\"'")
        if candidate:
            return candidate

        normalized_fallback = normalized
        for keyword in REMINDER_KEYWORDS:
            normalized_fallback = normalized_fallback.replace(keyword, " ")
        normalized_fallback = " ".join(normalized_fallback.split()).strip(" -,.")
        return normalized_fallback

    def _combine_datetime(
        self,
        remind_date,
        remind_time: str,
    ) -> datetime:
        hour_text, minute_text = remind_time.split(":", 1)
        return datetime(
            remind_date.year,
            remind_date.month,
            remind_date.day,
            int(hour_text),
            int(minute_text),
        )

    def _advance_recurrence(
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

    def _normalize(self, value: str) -> str:
        lowered = value.lower().translate(TURKISH_CHAR_MAP)
        return " ".join(lowered.split())
