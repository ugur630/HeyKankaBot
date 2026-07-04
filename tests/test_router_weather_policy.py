import unittest

from bot.core.tool_policy import ToolPolicyEngine


class RouterWeatherPolicyTests(unittest.TestCase):
    def test_weather_queries_are_forced_to_weather_tool(self) -> None:
        policy = ToolPolicyEngine()
        queries = (
            "simdi bakar misin Mersinde hava nasil",
            "Mersin hava nas\u0131l",
            "Mersin hava durumu",
            "Mersin'de ka\u00e7 derece",
            "Mersin s\u0131cakl\u0131k ne",
            "Mersin'de ya\u011fmur var m\u0131",
            "Mersin g\u00fcne\u015fli mi",
            "Mersin'de r\u00fczgar nas\u0131l",
        )

        for query in queries:
            with self.subTest(query=query):
                decision = policy.decide(query)
                self.assertIsNotNone(decision)
                self.assertEqual(decision["tool"], "weather")


if __name__ == "__main__":
    unittest.main()
