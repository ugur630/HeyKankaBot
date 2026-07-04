import logging
import os
from logging.handlers import RotatingFileHandler

from bot.config import LOGS_DIR

_LOG_LEVEL_NAMES = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}
_LOG_LEVEL = _LOG_LEVEL_NAMES.get(
    os.getenv("LOG_LEVEL", "INFO").strip().upper(),
    logging.INFO,
)

logger = logging.getLogger("HeyKanka")
logger.setLevel(_LOG_LEVEL)

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOGS_DIR / "bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
