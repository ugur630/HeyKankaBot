import unittest

from bot.core.reflection import ReflectionLayer


class ContradictionAwareFakeOllama:
    def generate_json(
        self,
        messages: list[dict[str, str]],
    ) -> dict[str, object]:
        context = messages[1]["content"]
        draft = messages[2]["content"]
        if "temperature_c: 33" in context and "26" in draft:
            return {
                "status": "RETRY",
                "reason": "Draft contradicts weather tool output.",
            }
        return {"status": "PASS"}


class ReflectionContradictionTests(unittest.TestCase):
    def test_reflection_returns_retry_for_tool_contradiction(self) -> None:
        reflection = ReflectionLayer(ContradictionAwareFakeOllama())
        decision = reflection.review(
            user_message="simdi bakar misin Mersinde hava nasil",
            context=[
                {
                    "role": "system",
                    "content": (
                        "The following information comes from a trusted system tool.\n"
                        "temperature_c: 33\n"
                        "condition: Sunny"
                    ),
                }
            ],
            draft_answer="Su anda Mersin'de hava 26°C.",
        )

        self.assertEqual(decision["status"], "RETRY")
        self.assertIn("contradicts", decision["reason"])


if __name__ == "__main__":
    unittest.main()
