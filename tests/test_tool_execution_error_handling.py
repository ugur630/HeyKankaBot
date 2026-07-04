import unittest

from bot.core.agent import AssistantAgent
from bot.core.reflection import ReflectionLayer
from bot.core.response_formatter import ResponseFormatter
from bot.core.tool_policy import ToolPolicyEngine
from bot.core.tool_router import ToolRouter
from bot.tools.registry import build_tool_registry
from tests._helpers import (
    FakeContextBuilder,
    FakeCurrencyService,
    FakeMemoryClassifier,
    FakeMemoryLifecycle,
    FakeReminderService,
    FakeSearchService,
    FakeWeatherService,
)


class UnknownToolCallOllama:
    def generate(self, messages: list[dict[str, str]]) -> str:
        del messages
        return (
            '<tool_call>{"tool":"time_machine","input":"go back"}'
            "</tool_call>"
        )

    def generate_yes_no(self, messages: list[dict[str, str]]) -> bool:
        del messages
        return False

    def generate_json(self, messages: list[dict[str, str]]) -> dict[str, object]:
        del messages
        return {"status": "PASS"}


class EmptyRememberPayloadOllama:
    def generate(self, messages: list[dict[str, str]]) -> str:
        del messages
        return '<tool_call>{"tool":"remember","input":""}</tool_call>'

    def generate_yes_no(self, messages: list[dict[str, str]]) -> bool:
        del messages
        return False

    def generate_json(self, messages: list[dict[str, str]]) -> dict[str, object]:
        del messages
        return {"status": "PASS"}


def _build_agent(ollama: object) -> AssistantAgent:
    tool_router = ToolRouter(
        build_tool_registry(
            memory_service=object(),  # unused: failures happen before use
            reminder_service=FakeReminderService(),
            search_service=FakeSearchService(),
            weather_service=FakeWeatherService(),
            currency_service=FakeCurrencyService(),
        )
    )
    return AssistantAgent(
        context_builder=FakeContextBuilder(),
        memory_classifier=FakeMemoryClassifier(),
        memory_lifecycle=FakeMemoryLifecycle(),
        reflection=ReflectionLayer(ollama),
        response_formatter=ResponseFormatter(),
        tool_policy=ToolPolicyEngine(),
        tool_router=tool_router,
        ollama_service=ollama,
    )


class ToolExecutionErrorHandlingTests(unittest.TestCase):
    def test_unknown_tool_call_degrades_to_friendly_message(self) -> None:
        agent = _build_agent(UnknownToolCallOllama())

        answer = agent.generate_reply(
            user_id=1,
            current_user_message="zamanda geri git",
        )

        self.assertEqual(answer, "Kanka, bu bilgiyi su an alamadim.")

    def test_tool_handler_exception_degrades_to_friendly_message(self) -> None:
        agent = _build_agent(EmptyRememberPayloadOllama())

        answer = agent.generate_reply(
            user_id=1,
            current_user_message="bunu hatirla",
        )

        self.assertEqual(answer, "Kanka, bu bilgiyi su an alamadim.")


if __name__ == "__main__":
    unittest.main()
