import json
import unittest

import httpx

from bot.services.weather_service import WeatherService


def _handler(request: httpx.Request) -> httpx.Response:
    if "geocoding-api" in str(request.url):
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Mersin",
                        "latitude": 36.8,
                        "longitude": 34.63,
                    }
                ]
            },
        )

    return httpx.Response(
        200,
        json={
            "current": {
                "time": "2026-07-04T12:00",
                "temperature_2m": 33.1,
                "relative_humidity_2m": 60,
                "apparent_temperature": 35.4,
                "weather_code": 1,
            }
        },
    )


def _no_results_handler(request: httpx.Request) -> httpx.Response:
    if "geocoding-api" in str(request.url):
        return httpx.Response(200, json={"results": []})
    return httpx.Response(200, json={})


def _http_error_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(500, text="internal error")


class WeatherServiceOpenMeteoTests(unittest.TestCase):
    def test_get_weather_uses_open_meteo_and_keeps_response_shape(self) -> None:
        service = WeatherService(transport=httpx.MockTransport(_handler))

        payload = json.loads(service.get_weather("Mersin hava nasil"))

        self.assertEqual(
            payload,
            {
                "city": "Mersin",
                "resolved_area": "Mersin",
                "temperature_c": 33.1,
                "feels_like_c": 35.4,
                "humidity": 60,
                "condition": "Genelde acik",
                "observation_time_utc": "2026-07-04T12:00",
                "source": "open-meteo",
            },
        )

    def test_get_weather_returns_error_when_city_not_found(self) -> None:
        service = WeatherService(
            transport=httpx.MockTransport(_no_results_handler)
        )

        payload = json.loads(service.get_weather("Nerede hava nasil"))

        self.assertIn("error", payload)

    def test_get_weather_returns_error_on_http_failure(self) -> None:
        service = WeatherService(
            transport=httpx.MockTransport(_http_error_handler)
        )

        payload = json.loads(service.get_weather("Mersin hava nasil"))

        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
