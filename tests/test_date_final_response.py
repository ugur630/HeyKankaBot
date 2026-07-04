import unittest

from tests._helpers import build_test_agent


class DateFinalResponseTests(unittest.TestCase):
    def test_date_returns_tool_output_without_llm_generation(self) -> None:
        agent, ollama = build_test_agent()

        answer = agent.generate_reply(
            user_id=1,
            current_user_message="peki tarih kac",
        )

        self.assertIn("Bugunun tarihi:", answer)
        self.assertEqual(ollama.generate_calls, [])


if __name__ == "__main__":
    unittest.main()
