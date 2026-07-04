from collections.abc import Callable
from dataclasses import dataclass

from bot.services.currency_service import CurrencyService
from bot.services.memory_service import MemoryService
from bot.services.reminder_service import ReminderService
from bot.services.search_service import SearchService
from bot.services.weather_service import WeatherService
from bot.tools.calculator import calculate
from bot.tools.clock import get_current_time
from bot.tools.currency import get_currency_rate
from bot.tools.date import get_current_date
from bot.tools.reminder import create_reminder
from bot.tools.weather import get_weather


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_hint: str
    handler: Callable[[str, int | None], str]
    final_response: bool = False


def build_tool_registry(
    memory_service: MemoryService,
    reminder_service: ReminderService,
    search_service: SearchService,
    weather_service: WeatherService,
    currency_service: CurrencyService,
) -> dict[str, ToolDefinition]:
    def clock_tool(query: str, user_id: int | None) -> str:
        del user_id
        return get_current_time(query)

    def date_tool(query: str, user_id: int | None) -> str:
        del user_id
        return get_current_date(query)

    def calculator_tool(expression: str, user_id: int | None) -> str:
        del user_id
        return calculate(expression)

    def weather_tool(query: str, user_id: int | None) -> str:
        del user_id
        return get_weather(query, weather_service)

    def currency_tool(query: str, user_id: int | None) -> str:
        del user_id
        return get_currency_rate(query, currency_service)

    def reminder_tool(query: str, user_id: int | None) -> str:
        if user_id is None:
            raise ValueError("User id is required for reminder tool.")

        return create_reminder(
            query=query,
            user_id=user_id,
            chat_id=user_id,
            reminder_service=reminder_service,
        )

    def remember_tool(payload: str, user_id: int | None) -> str:
        if user_id is None:
            raise ValueError("User id is required for remember tool.")

        key, value = _parse_memory_payload(payload)
        memory_service.remember(
            user_id=user_id,
            key=key,
            value=value,
            importance=1,
        )
        return f"Memory saved: {key} = {value}"

    def recall_tool(query: str, user_id: int | None) -> str:
        if user_id is None:
            raise ValueError("User id is required for recall tool.")

        memories = memory_service.recall(
            user_id=user_id,
            query=query,
        )
        if not memories:
            return "No memories found."

        lines = ["Relevant memories:"]
        for item in memories:
            lines.append(f"- {item['key']}: {item['value']}")
        return "\n".join(lines)

    def search_web_tool(query: str, user_id: int | None) -> str:
        del user_id
        return search_service.format_results(query)

    return {
        "clock": ToolDefinition(
            name="clock",
            description="Returns the current system time.",
            input_hint="Use for questions like 'what time is it?'",
            handler=clock_tool,
            final_response=True,
        ),
        "date": ToolDefinition(
            name="date",
            description="Returns the current system date.",
            input_hint="Use for questions like 'what is today's date?'",
            handler=date_tool,
            final_response=True,
        ),
        "calculator": ToolDefinition(
            name="calculator",
            description="Evaluates basic arithmetic expressions.",
            input_hint="Use inputs like '23*18' or '(12+5)/3'.",
            handler=calculator_tool,
            final_response=True,
        ),
        "weather": ToolDefinition(
            name="weather",
            description="Returns current weather information for a location.",
            input_hint="Use for weather questions and include the city/location.",
            handler=weather_tool,
            final_response=True,
        ),
        "currency": ToolDefinition(
            name="currency",
            description="Returns the current exchange rate between two currencies.",
            input_hint=(
                "Use for exchange rate questions like 'dolar kac tl'."
            ),
            handler=currency_tool,
            final_response=True,
        ),
        "reminder": ToolDefinition(
            name="reminder",
            description="Creates a reminder and stores it for later delivery.",
            input_hint=(
                "Use for reminder requests like "
                "'yarin 09:30'da ilac almayi hatirlat'."
            ),
            handler=reminder_tool,
            final_response=True,
        ),
        "remember": ToolDefinition(
            name="remember",
            description="Saves durable user information into long-term memory.",
            input_hint="Use 'key | value' format, like 'name | Ugur'.",
            handler=remember_tool,
        ),
        "recall": ToolDefinition(
            name="recall",
            description="Loads durable user information from long-term memory.",
            input_hint="Use a short query like 'coffee' or 'wife'.",
            handler=recall_tool,
        ),
        "search_web": ToolDefinition(
            name="search_web",
            description="Searches the web for fresh or current information.",
            input_hint="Use the user's question or a focused search query.",
            handler=search_web_tool,
        ),
    }


def _parse_memory_payload(payload: str) -> tuple[str, str]:
    if "|" in payload:
        key, value = payload.split("|", 1)
    elif ":" in payload:
        key, value = payload.split(":", 1)
    else:
        key = "note"
        value = payload

    normalized_key = key.strip().lower() or "note"
    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError("Memory value is empty.")

    return normalized_key, normalized_value
