import json
import unittest

import httpx

from bot.services.currency_service import CurrencyService


def _handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "amount": 1.0,
            "base": "USD",
            "date": "2026-07-04",
            "rates": {"TRY": 32.45},
        },
    )


def _http_error_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(500, text="internal error")


class CurrencyServiceGetRateTests(unittest.TestCase):
    def test_get_rate_returns_expected_shape_on_success(self) -> None:
        service = CurrencyService(transport=httpx.MockTransport(_handler))

        payload = json.loads(service.get_rate("usd", "try"))

        self.assertEqual(
            payload,
            {
                "from": "USD",
                "to": "TRY",
                "rate": 32.45,
                "date": "2026-07-04",
                "source": "frankfurter",
            },
        )

    def test_get_rate_returns_error_on_http_failure(self) -> None:
        service = CurrencyService(
            transport=httpx.MockTransport(_http_error_handler)
        )

        payload = json.loads(service.get_rate("usd", "try"))

        self.assertIn("error", payload)

    def test_get_rate_rejects_gold_as_unsupported(self) -> None:
        service = CurrencyService(transport=httpx.MockTransport(_handler))

        payload = json.loads(service.get_rate("xau", "try"))

        self.assertIn("error", payload)


class CurrencyServiceExtractCurrenciesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = CurrencyService()

    def test_extracts_single_currency_with_default_target_try(self) -> None:
        self.assertEqual(
            self.service.extract_currencies("dolar kac tl"),
            ("USD", "TRY"),
        )

    def test_extracts_explicit_currency_pair_in_order(self) -> None:
        self.assertEqual(
            self.service.extract_currencies("1 dolar kac euro eder"),
            ("USD", "EUR"),
        )

    def test_returns_none_when_no_currency_found(self) -> None:
        self.assertIsNone(
            self.service.extract_currencies("bugun hava nasil")
        )


if __name__ == "__main__":
    unittest.main()
