import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
BOT_DIR = BASE_DIR / "bot"
DATA_DIR = BOT_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
DATABASE_PATH = DATA_DIR / "memory.db"


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    ollama_model: str = "gemma3:12b"
    conversation_limit: int = 20
    memory_limit: int = 5
    search_result_limit: int = 5
    default_city: str = ""
    default_timezone: str = "Europe/Istanbul"
    default_language: str = "tr"
    default_reminder_time: str = "09:00"
    default_chat_id: int | None = None
    notification_time: str = "08:00"
    scheduler_poll_interval_seconds: int = 30
    http_timeout_seconds: float = 10.0
    job_retry_limit: int = 0
    feature_morning_weather_enabled: bool = True
    feature_reminder_dispatcher_enabled: bool = True
    database_path: Path = DATABASE_PATH
    logs_dir: Path = LOGS_DIR


def get_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    model = os.getenv("OLLAMA_MODEL", "gemma3:12b").strip()
    default_city = os.getenv("DEFAULT_CITY", "").strip()
    default_timezone = (
        os.getenv("DEFAULT_TIMEZONE", "Europe/Istanbul").strip()
        or "Europe/Istanbul"
    )
    default_language = (
        os.getenv("DEFAULT_LANGUAGE", "tr").strip() or "tr"
    )
    default_reminder_time = (
        os.getenv("DEFAULT_REMINDER_TIME", "09:00").strip() or "09:00"
    )
    default_chat_id = _parse_optional_int(
        os.getenv("DEFAULT_CHAT_ID", "").strip()
    )
    notification_time = (
        os.getenv("NOTIFICATION_TIME", "08:00").strip() or "08:00"
    )
    scheduler_poll_interval_seconds = int(
        os.getenv("SCHEDULER_POLL_INTERVAL_SECONDS", "30").strip() or "30"
    )
    http_timeout_seconds = float(
        os.getenv("HTTP_TIMEOUT_SECONDS", "10.0").strip() or "10.0"
    )
    job_retry_limit = int(
        os.getenv("JOB_RETRY_LIMIT", "0").strip() or "0"
    )
    feature_morning_weather_enabled = _parse_bool(
        os.getenv("FEATURE_MORNING_WEATHER_ENABLED", "true").strip()
    )
    feature_reminder_dispatcher_enabled = _parse_bool(
        os.getenv("FEATURE_REMINDER_DISPATCHER_ENABLED", "true").strip()
    )

    return Settings(
        telegram_bot_token=token,
        ollama_model=model or "gemma3:12b",
        default_city=default_city,
        default_timezone=default_timezone,
        default_language=default_language,
        default_reminder_time=default_reminder_time,
        default_chat_id=default_chat_id,
        notification_time=notification_time,
        scheduler_poll_interval_seconds=scheduler_poll_interval_seconds,
        http_timeout_seconds=http_timeout_seconds,
        job_retry_limit=job_retry_limit,
        feature_morning_weather_enabled=feature_morning_weather_enabled,
        feature_reminder_dispatcher_enabled=feature_reminder_dispatcher_enabled,
    )


def ensure_runtime_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _parse_optional_int(value: str) -> int | None:
    if not value:
        return None

    return int(value)


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
