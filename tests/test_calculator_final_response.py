import unittest

from tests._helpers import build_test_agent


class CalculatorFinalResponseTests(unittest.TestCase):
    def test_calculator_returns_direct_result_without_llm_generation(
        self,
    ) -> None:
        agent, ollama = build_test_agent()

        answer = agent.generate_reply(
            user_id=1,
            current_user_message="23*18",
        )

        self.assertEqual(answer, "23*18 = 414")
        self.assertEqual(len(ollama.generate_calls), 2)


if __name__ == "__main__":
    unittest.main()
