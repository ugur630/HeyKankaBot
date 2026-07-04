import unittest

from bot.core.context_builder import ContextBuilder


class FakeMemoryService:
    def load_history(
        self,
        user_id: int,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        return []

    def search(
        self,
        user_id: int,
        query: str,
        limit: int | None = None,
    ) -> list[dict[str, str | int]]:
        return []

    def recall(
        self,
        user_id: int,
        query: str = "",
        limit: int | None = None,
    ) -> list[dict[str, str | int]]:
        return []


class ToolOutputInjectionTests(unittest.TestCase):
    def test_tool_result_is_injected_before_user_message(self) -> None:
        builder = ContextBuilder(FakeMemoryService())
        messages = builder.build_tool_followup_messages(
            user_id=1,
            current_user_message="what time is it",
            tool_name="clock",
            tool_input="what time is it",
            tool_output='{"time":"10:52:26"}',
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "system")
        self.assertIn("Current Time: 10:52:26", messages[1]["content"])
        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"], "what time is it")


if __name__ == "__main__":
    unittest.main()
