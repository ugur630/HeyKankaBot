import unittest

from bot.core.tool_policy import ToolPolicyEngine


class RouterCurrencyPolicyTests(unittest.TestCase):
    def test_currency_questions_are_forced_to_currency_tool(self) -> None:
        policy = ToolPolicyEngine()
        queries = (
            "dolar kac tl",
            "euro ne kadar",
            "sterlin kac lira",
            "1 dolar kac euro eder",
        )

        for query in queries:
            with self.subTest(query=query):
                decision = policy.decide(query)
                self.assertIsNotNone(decision)
                self.assertEqual(decision["tool"], "currency")

    def test_crypto_questions_still_fall_back_to_search_web(self) -> None:
        policy = ToolPolicyEngine()
        queries = (
            "bitcoin kac dolar",
            "en iyi kripto hangisi",
        )

        for query in queries:
            with self.subTest(query=query):
                decision = policy.decide(query)
                self.assertIsNotNone(decision)
                self.assertEqual(decision["tool"], "search_web")

    def test_general_market_questions_still_fall_back_to_search_web(
        self,
    ) -> None:
        policy = ToolPolicyEngine()
        queries = ("borsa nasil", "hisse senetleri nasil")

        for query in queries:
            with self.subTest(query=query):
                decision = policy.decide(query)
                self.assertIsNotNone(decision)
                self.assertEqual(decision["tool"], "search_web")


if __name__ == "__main__":
    unittest.main()
