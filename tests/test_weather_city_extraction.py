import unittest

from bot.services.weather_service import WeatherService


class WeatherCityExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = WeatherService()

    def test_extracts_city_from_turkish_weather_queries(self) -> None:
        cases = {
            "Mersin hava nasil": "Mersin",
            "\u0130stanbul hava nas\u0131l": "\u0130stanbul",
            "Ankara'da ka\u00e7 derece": "Ankara",
            "\u0130zmir hava durumu": "\u0130zmir",
            "Mersin hava durumu": "Mersin",
            "Mersin'de ya\u011fmur var m\u0131": "Mersin",
            "Mersin g\u00fcne\u015fli mi": "Mersin",
            "Mersin'de r\u00fczgar nas\u0131l": "Mersin",
        }

        for query, expected_city in cases.items():
            with self.subTest(query=query):
                self.assertEqual(
                    self.service.extract_city(query),
                    expected_city,
                )

    def test_ignores_weather_words_as_city_names(self) -> None:
        cases = (
            "hava nasil",
            "ka\u00e7 derece",
            "s\u0131cakl\u0131k ne",
            "bugun ya\u011fmur var m\u0131",
            "yar\u0131n g\u00fcne\u015fli mi",
        )

        for query in cases:
            with self.subTest(query=query):
                self.assertEqual(self.service.extract_city(query), "")


if __name__ == "__main__":
    unittest.main()
