from bot.core.agent import AssistantAgent
from bot.core.memory_classifier import MemoryClassifier
from bot.core.memory_lifecycle import MemoryLifecycle
from bot.core.reflection import ReflectionLayer
from bot.core.response_formatter import ResponseFormatter
from bot.core.tool_policy import ToolPolicyEngine
from bot.core.tool_router import ToolRouter
from bot.services.search_service import SearchService
from bot.services.weather_service import WeatherService
from bot.tools.registry import build_tool_registry


class FakeContextBuilder:
    def build_messages(
        self,
        user_id: int,
        current_user_message: str,
        tool_instructions: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": tool_instructions},
            {"role": "user", "content": current_user_message},
        ]

    def build_tool_followup_messages(
        self,
        user_id: int,
        current_user_message: str,
        tool_name: str,
        tool_input: str,
        tool_output: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": f"Tool Name: {tool_name}"},
            {"role": "system", "content": f"Tool Output: {tool_output}"},
            {"role": "user", "content": current_user_message},
        ]

    def build_search_decision_messages(
        self,
        user_id: int,
        current_user_message: str,
    ) -> list[dict[str, str]]:
        return [{"role": "user", "content": current_user_message}]

    def build_search_followup_messages(
        self,
        user_id: int,
        current_user_message: str,
        search_results: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": search_results},
            {"role": "user", "content": current_user_message},
        ]


class FakeMemoryClassifier:
    def classify(self, user_message: str) -> dict[str, str]:
        return {"importance": "NO_MEMORY"}


class FakeMemoryLifecycle:
    def apply(
        self,
        user_id: int,
        memory_payload: dict[str, str],
    ) -> dict[str, str | int | bool]:
        return {"action": "IGNORE", "stored": False}


class FakeOllamaService:
    def __init__(self) -> None:
        self.generate_calls: list[list[dict[str, str]]] = []

    def generate(self, messages: list[dict[str, str]]) -> str:
        self.generate_calls.append(messages)
        last_user_message = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user_message = message.get("content", "")
                break
        if last_user_message.strip() == "23*18":
            return '<tool_call>{"tool":"calculator","input":"23*18"}</tool_call>'
        return "llm-output"

    def generate_yes_no(self, messages: list[dict[str, str]]) -> bool:
        self.generate_calls.append(messages)
        return False

    def generate_json(
        self,
        messages: list[dict[str, str]],
    ) -> dict[str, object]:
        self.generate_calls.append(messages)
        return {"status": "PASS"}


class FakeSearchService(SearchService):
    def __init__(self) -> None:
        super().__init__(max_results=2)

    def format_results(self, query: str) -> str:
        return '{"query":"test","results":[]}'


class FakeWeatherService(WeatherService):
    def get_weather(self, location_query: str) -> str:
        return (
            '{"city":"Mersin","temperature_c":"33",'
            '"feels_like_c":"35","humidity":"60",'
            '"condition":"Sunny","source":"test"}'
        )


class FakeCurrencyService:
    def extract_currencies(self, query: str) -> tuple[str, str] | None:
        del query
        return ("USD", "TRY")

    def get_rate(self, from_currency: str, to_currency: str) -> str:
        del from_currency, to_currency
        return (
            '{"from":"USD","to":"TRY","rate":32.45,'
            '"date":"2026-07-04","source":"frankfurter"}'
        )


class FakeReminderService:
    def create_reminder(
        self,
        *,
        user_id: int,
        chat_id: int,
        request_text: str,
        now=None,
    ) -> str:
        del now
        return (
            '{"status":"scheduled","reminder_id":"1",'
            f'"message":"{request_text}","remind_at":"2026-07-05 09:00",'
            '"recurrence":"none"}'
        )


def build_test_agent() -> tuple[AssistantAgent, FakeOllamaService]:
    ollama = FakeOllamaService()
    tool_router = ToolRouter(
        build_tool_registry(
            memory_service=object(),  # unused in these tests
            reminder_service=FakeReminderService(),
            search_service=FakeSearchService(),
            weather_service=FakeWeatherService(),
            currency_service=FakeCurrencyService(),
        )
    )
    agent = AssistantAgent(
        context_builder=FakeContextBuilder(),
        memory_classifier=FakeMemoryClassifier(),
        memory_lifecycle=FakeMemoryLifecycle(),
        reflection=ReflectionLayer(ollama),
        response_formatter=ResponseFormatter(),
        tool_policy=ToolPolicyEngine(),
        tool_router=tool_router,
        ollama_service=ollama,
    )
    return agent, ollama
