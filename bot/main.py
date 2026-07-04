from bot.config import ensure_runtime_directories, get_settings
from bot.database.database import initialize_database
from bot.services.telegram_service import build_application
from bot.utils.logger import logger


def main() -> None:
    settings = get_settings()
    ensure_runtime_directories()

    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    database = initialize_database(settings.database_path)

    logger.info("HeyKankaBot starting")
    application = build_application(settings, database)
    application.run_polling()


if __name__ == "__main__":
    main()
