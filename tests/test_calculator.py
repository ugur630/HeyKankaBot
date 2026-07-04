import json
import unittest

from bot.tools.calculator import calculate


class CalculatorTests(unittest.TestCase):
    def test_evaluates_basic_expression(self) -> None:
        payload = json.loads(calculate("23*18"))
        self.assertEqual(payload["result"], "414")

    def test_rejects_power_operator(self) -> None:
        payload = json.loads(calculate("9**9**9"))
        self.assertIn("error", payload)
        self.assertNotIn("result", payload)

    def test_rejects_expressions_longer_than_limit(self) -> None:
        long_expression = "1+" * 40 + "1"
        payload = json.loads(calculate(long_expression))
        self.assertIn("error", payload)
        self.assertNotIn("result", payload)

    def test_rejects_letters_and_builtins(self) -> None:
        payload = json.loads(calculate("__import__('os')"))
        self.assertIn("error", payload)
        self.assertNotIn("result", payload)


if __name__ == "__main__":
    unittest.main()
