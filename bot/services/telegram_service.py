from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import Settings
from bot.core.agent import AssistantAgent
from bot.core.context_builder import ContextBuilder
from bot.core.memory_classifier import MemoryClassifier
from bot.core.memory_lifecycle import MemoryLifecycle
from bot.core.reflection import ReflectionLayer
from bot.core.response_formatter import ResponseFormatter
from bot.core.tool_policy import ToolPolicyEngine
from bot.core.tool_router import ToolRouter
from bot.database.database import Database
from bot.handlers.message_handler import handle_message, start
from bot.services.memory_service import MemoryService
from bot.services.ollama_service import OllamaService
from bot.services.profile_service import ProfileService
from bot.services.reminder_parser import ReminderParser
from bot.services.reminder_service import ReminderService
from bot.services.search_service import SearchService
from bot.services.weather_service import WeatherService
from bot.repositories.reminder_repository import ReminderRepository
from bot.repositories.user_profile_repository import UserProfileRepository
from bot.tools.registry import build_tool_registry


def build_application(
    settings: Settings,
    database: Database,
) -> Application:
    memory_service = MemoryService(
        database=database,
        history_limit=settings.conversation_limit,
        message_retention=50,
        memory_limit=settings.memory_limit,
    )
    user_profile_repository = UserProfileRepository(database)
    reminder_repository = ReminderRepository(database)
    profile_service = ProfileService(
        repository=user_profile_repository,
        settings=settings,
    )
    reminder_service = ReminderService(
        repository=reminder_repository,
        profile_service=profile_service,
        parser=ReminderParser(),
    )
    search_service = SearchService(
        max_results=settings.search_result_limit,
        timeout_seconds=settings.http_timeout_seconds,
    )
    weather_service = WeatherService(
        default_city=settings.default_city,
        timeout_seconds=settings.http_timeout_seconds,
    )

    tool_router = ToolRouter(
        build_tool_registry(
            memory_service=memory_service,
            reminder_service=reminder_service,
            search_service=search_service,
            weather_service=weather_service,
        )
    )
    context_builder = ContextBuilder(memory_service)
    ollama_service = OllamaService(settings.ollama_model)
    memory_classifier = MemoryClassifier(ollama_service)
    memory_lifecycle = MemoryLifecycle(memory_service, ollama_service)
    reflection = ReflectionLayer(ollama_service)
    response_formatter = ResponseFormatter()
    tool_policy = ToolPolicyEngine()
    agent = AssistantAgent(
        context_builder=context_builder,
        memory_classifier=memory_classifier,
        memory_lifecycle=memory_lifecycle,
        reflection=reflection,
        response_formatter=response_formatter,
        tool_policy=tool_policy,
        tool_router=tool_router,
        ollama_service=ollama_service,
    )

    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .build()
    )

    application.bot_data["memory_service"] = memory_service
    application.bot_data["agent"] = agent
    application.bot_data["profile_service"] = profile_service

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    return application
