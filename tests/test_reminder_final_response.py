import unittest

from tests._helpers import build_test_agent


class ReminderFinalResponseTests(unittest.TestCase):
    def test_reminder_returns_tool_output_without_llm_generation(self) -> None:
        agent, ollama = build_test_agent()

        answer = agent.generate_reply(
            user_id=1,
            current_user_message="yarin 09:30'da ilac almayi hatirlat",
        )

        self.assertIn("Kanka, hatirlatmayi kaydettim.", answer)
        self.assertIn("- Zaman: 2026-07-05 09:00", answer)
        self.assertEqual(ollama.generate_calls, [])


if __name__ == "__main__":
    unittest.main()
