import unittest

from tests._helpers import build_test_agent


class WeatherFinalResponseTests(unittest.TestCase):
    def test_weather_returns_tool_output_without_llm_generation(self) -> None:
        agent, ollama = build_test_agent()

        answer = agent.generate_reply(
            user_id=1,
            current_user_message="bugun Mersinde hava kac derece",
        )

        self.assertIn("Kanka, su an Mersin'de:", answer)
        self.assertIn("- Sicaklik: 33 C", answer)
        self.assertIn("- Hissedilen: 35 C", answer)
        self.assertIn("- Nem: %60", answer)
        self.assertEqual(ollama.generate_calls, [])


if __name__ == "__main__":
    unittest.main()
