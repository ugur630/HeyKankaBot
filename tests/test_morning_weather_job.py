import unittest

from bot.config import Settings
from bot.jobs import JobContext
from bot.jobs.morning_weather import MorningWeatherJob


class FakeWeatherService:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def get_weather(self, city: str) -> str:
        self.queries.append(city)
        return '{"city":"Mersin","temperature_c":"31"}'


class FakeFormatter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def format_tool_response(self, tool_name: str, raw_output: str) -> str:
        self.calls.append((tool_name, raw_output))
        return "Kanka, su an Mersin'de:\n- Sicaklik: 31 C"


class FakeTelegramSender:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    def send_text(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


class MorningWeatherJobTests(unittest.TestCase):
    def test_job_reuses_weather_service_formatter_and_sender(self) -> None:
        weather_service = FakeWeatherService()
        formatter = FakeFormatter()
        sender = FakeTelegramSender()
        context = JobContext(
            settings=Settings(
                telegram_bot_token="token",
                default_city="Mersin",
                default_chat_id=42,
            ),
            profile_service=object(),
            reminder_service=object(),
            weather_service=weather_service,
            search_service=object(),
            response_formatter=formatter,
            telegram_sender=sender,
        )

        job = MorningWeatherJob(context)
        job.run()

        self.assertEqual(weather_service.queries, ["Mersin"])
        self.assertEqual(
            formatter.calls,
            [("weather", '{"city":"Mersin","temperature_c":"31"}')],
        )
        self.assertEqual(
            sender.messages,
            [(42, "Gunaydin!\n\nKanka, su an Mersin'de:\n- Sicaklik: 31 C")],
        )


if __name__ == "__main__":
    unittest.main()
