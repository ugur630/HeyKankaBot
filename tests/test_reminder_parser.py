import unittest
from datetime import datetime, timedelta

from bot.services.reminder_parser import ReminderParser


class ReminderParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = ReminderParser()
        self.now = datetime(2026, 7, 4, 10, 0)

    def test_parses_relative_day_and_time(self) -> None:
        result = self.parser.parse(
            "Yarin 09:30'da ilac almayi hatirlat",
            now=self.now,
            default_time="09:00",
        )

        self.assertEqual(result.message, "ilac almayi")
        self.assertEqual(result.remind_at, datetime(2026, 7, 5, 9, 30))
        self.assertEqual(result.recurrence, "none")

    def test_uses_default_time_when_missing(self) -> None:
        result = self.parser.parse(
            "yarin faturayi odemeyi hatirlat",
            now=self.now,
            default_time="18:45",
        )

        self.assertEqual(result.message, "faturayi odemeyi")
        self.assertEqual(result.remind_at, datetime(2026, 7, 5, 18, 45))

    def test_detects_recurrence(self) -> None:
        result = self.parser.parse(
            "Her hafta 08:00'de spor yapmayi hatirlat",
            now=self.now,
            default_time="09:00",
        )

        self.assertEqual(result.recurrence, "weekly")
        self.assertEqual(result.message, "spor yapmayi")

    def test_strips_greeting_and_question_suffix_from_message(self) -> None:
        result = self.parser.parse(
            "Selam kanka bana 1 dakika sonra su icmeyi hatirlatir misin",
            now=self.now,
            default_time="09:00",
        )

        self.assertEqual(result.message, "su icmeyi")
        self.assertEqual(result.remind_at, self.now + timedelta(minutes=1))


if __name__ == "__main__":
    unittest.main()
