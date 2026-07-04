import unittest

from tests._helpers import build_test_agent


class ClockFinalResponseTests(unittest.TestCase):
    def test_clock_returns_tool_output_without_llm_generation(self) -> None:
        agent, ollama = build_test_agent()

        answer = agent.generate_reply(
            user_id=1,
            current_user_message="saat kac simdi",
        )

        self.assertIn("Su an saat:", answer)
        self.assertEqual(ollama.generate_calls, [])


if __name__ == "__main__":
    unittest.main()
