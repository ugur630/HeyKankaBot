import json
import re
import time

import httpx

from bot.utils.logger import logger

FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"

TURKISH_CHAR_MAP = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }
)

CURRENCY_ALIASES = {
    "amerikan dolari": "USD",
    "dolar": "USD",
    "usd": "USD",
    "avro": "EUR",
    "euro": "EUR",
    "eur": "EUR",
    "ingiliz sterlini": "GBP",
    "sterlin": "GBP",
    "gbp": "GBP",
    "altin": "XAU",
    "xau": "XAU",
    "lira": "TRY",
    "tl": "TRY",
    "try": "TRY",
}

UNSUPPORTED_CURRENCY_ERROR = (
    "Su an sadece doviz kurlarini destekliyorum."
)


class CurrencyService:
    def __init__(
        self,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self._transport = transport

    def get_rate(self, from_currency: str, to_currency: str) -> str:
        from_code = from_currency.strip().upper()
        to_code = to_currency.strip().upper()

        if from_code == "XAU" or to_code == "XAU":
            return json.dumps({"error": UNSUPPORTED_CURRENCY_ERROR})

        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                transport=self._transport,
            ) as client:
                started_at = time.perf_counter()
                response = client.get(
                    FRANKFURTER_URL,
                    params={"base": from_code, "symbols": to_code},
                )
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                logger.info("Currency HTTP status: %s", response.status_code)
                logger.info("Currency response time: %.2f ms", elapsed_ms)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            return json.dumps(
                {
                    "error": (
                        "Kur bilgisi su an alinamadi: "
                        f"{exc}"
                    ),
                }
            )
        except ValueError:
            return json.dumps(
                {
                    "error": "Currency service returned invalid data.",
                }
            )

        rates = payload.get("rates") or {}
        rate = rates.get(to_code)
        if rate is None:
            return json.dumps(
                {
                    "error": (
                        f"{from_code}/{to_code} icin kur bilgisi bulamadim."
                    ),
                }
            )

        result = {
            "from": from_code,
            "to": to_code,
            "rate": rate,
            "date": payload.get("date"),
            "source": "frankfurter",
        }
        return json.dumps(result)

    def extract_currencies(self, query: str) -> tuple[str, str] | None:
        normalized = self._normalize(query)

        matches: list[tuple[int, str]] = []
        for alias, code in CURRENCY_ALIASES.items():
            for match in re.finditer(rf"\b{re.escape(alias)}\b", normalized):
                matches.append((match.start(), code))
        matches.sort(key=lambda item: item[0])

        ordered_codes: list[str] = []
        for _, code in matches:
            if code not in ordered_codes:
                ordered_codes.append(code)

        if not ordered_codes:
            return None
        if len(ordered_codes) == 1:
            return (ordered_codes[0], "TRY")
        return (ordered_codes[0], ordered_codes[1])

    def _normalize(self, value: str) -> str:
        lowered = value.lower().translate(TURKISH_CHAR_MAP)
        return " ".join(lowered.split())
