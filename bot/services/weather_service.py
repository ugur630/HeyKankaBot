import json
import re
import time
from urllib.parse import quote_plus

import httpx

from bot.utils.logger import logger


LOCATION_SUFFIXES = (
    "de",
    "da",
    "te",
    "ta",
    "den",
    "dan",
    "ten",
    "tan",
)

WEATHER_MARKERS = {
    "hava",
    "durumu",
    "nasil",
    "kac",
    "derece",
    "sicaklik",
    "yagmur",
    "gunesli",
    "ruzgar",
    "bugun",
    "yarin",
}

FILLER_WORDS = {
    "bakar",
    "misin",
    "peki",
    "su",
    "an",
    "simdi",
    "bir",
    "de",
    "da",
    "mi",
    "mu",
    "muu",
    "midir",
    "icin",
    "var",
    "bu",
    "orada",
}

TURKISH_CHAR_MAP = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "İ": "I",
    }
)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_WEATHER_DESCRIPTIONS = {
    0: "Acik",
    1: "Genelde acik",
    2: "Parcali bulutlu",
    3: "Kapali",
    45: "Sisli",
    48: "Kiragi sisi",
    51: "Hafif cisenti",
    53: "Cisenti",
    55: "Yogun cisenti",
    56: "Hafif donan cisenti",
    57: "Donan cisenti",
    61: "Hafif yagmurlu",
    63: "Yagmurlu",
    65: "Siddetli yagmurlu",
    66: "Hafif donan yagmur",
    67: "Donan yagmur",
    71: "Hafif kar yagisli",
    73: "Kar yagisli",
    75: "Yogun kar yagisli",
    77: "Kar taneli",
    80: "Hafif saganak yagmurlu",
    81: "Saganak yagmurlu",
    82: "Siddetli saganak yagmurlu",
    85: "Hafif kar saganagi",
    86: "Yogun kar saganagi",
    95: "Gok gurultulu firtina",
    96: "Dolulu gok gurultulu firtina",
    99: "Siddetli dolulu firtina",
}


def describe_weather_code(weather_code: object) -> str:
    try:
        code = int(weather_code)
    except (TypeError, ValueError):
        return ""

    if code in WMO_WEATHER_DESCRIPTIONS:
        return WMO_WEATHER_DESCRIPTIONS[code]

    if 1 <= code <= 3:
        return "Parcali bulutlu"
    if code in (45, 48):
        return "Sisli"
    if 51 <= code <= 67:
        return "Yagmurlu"
    if 71 <= code <= 77:
        return "Kar yagisli"
    if 80 <= code <= 82:
        return "Saganak yagmurlu"
    if 95 <= code <= 99:
        return "Firtinali"
    return ""


class WeatherService:
    def __init__(
        self,
        default_city: str | None = None,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.default_city = default_city.strip() if default_city else None
        self.timeout_seconds = timeout_seconds
        self._transport = transport

    def get_weather(self, location_query: str) -> str:
        normalized = location_query.strip()
        city = self.extract_city(normalized)
        logger.info("Extracted city: %s", city or "(missing)")

        if not city and self.default_city:
            city = self.default_city
            logger.info("Weather default city applied: %s", city)

        if not city:
            return json.dumps(
                {
                    "error": (
                        "Hava durumuna bakmam icin sehri de yazar misin?"
                    ),
                }
            )

        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=self.timeout_seconds,
                headers={"User-Agent": "HeyKankaBot/0.7"},
                transport=self._transport,
            ) as client:
                location = self._geocode_city(client, city)
                if location is None:
                    return json.dumps(
                        {
                            "error": (
                                f"{city} icin konum bulamadim, sehir "
                                "adini kontrol edebilir misin?"
                            ),
                        }
                    )

                current = self._fetch_current_weather(
                    client,
                    latitude=location["latitude"],
                    longitude=location["longitude"],
                )
        except httpx.HTTPError as exc:
            return json.dumps(
                {
                    "error": (
                        "Weather information could not be retrieved: "
                        f"{exc}"
                    ),
                }
            )
        except ValueError:
            return json.dumps(
                {
                    "error": "Weather service returned invalid data.",
                }
            )

        result = {
            "city": city,
            "resolved_area": location.get("resolved_area") or city,
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "condition": describe_weather_code(current.get("weather_code")),
            "observation_time_utc": current.get("time"),
            "source": "open-meteo",
        }

        return json.dumps(result)

    def _geocode_city(
        self,
        client: httpx.Client,
        city: str,
    ) -> dict[str, object] | None:
        started_at = time.perf_counter()
        response = client.get(
            GEOCODING_URL,
            params={
                "name": city,
                "count": 1,
                "language": "tr",
            },
        )
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info("Geocoding HTTP status: %s", response.status_code)
        logger.info("Geocoding response time: %.2f ms", elapsed_ms)
        response.raise_for_status()

        payload = response.json()
        results = payload.get("results") or []
        if not results:
            return None

        match = results[0]
        return {
            "latitude": match["latitude"],
            "longitude": match["longitude"],
            "resolved_area": match.get("name"),
        }

    def _fetch_current_weather(
        self,
        client: httpx.Client,
        *,
        latitude: float,
        longitude: float,
    ) -> dict[str, object]:
        started_at = time.perf_counter()
        response = client.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,weather_code"
                ),
                "timezone": "auto",
            },
        )
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info("Forecast HTTP status: %s", response.status_code)
        logger.info("Forecast response time: %.2f ms", elapsed_ms)
        response.raise_for_status()

        payload = response.json()
        return payload.get("current") or {}

    def extract_city(self, query: str) -> str:
        tokens = self._tokenize(query)
        if not tokens:
            return ""

        marker_indexes = [
            index
            for index, token in enumerate(tokens)
            if token["normalized"] in WEATHER_MARKERS
        ]

        if marker_indexes:
            for marker_index in marker_indexes:
                candidate = self._find_candidate_before_marker(
                    tokens=tokens,
                    marker_index=marker_index,
                )
                if candidate:
                    return candidate

        for token in tokens:
            if self._is_valid_city_token(token["normalized"]):
                return token["display"]

        return ""

    def _find_candidate_before_marker(
        self,
        tokens: list[dict[str, str]],
        marker_index: int,
    ) -> str:
        for index in range(marker_index - 1, -1, -1):
            candidate = tokens[index]
            if self._is_valid_city_token(candidate["normalized"]):
                return candidate["display"]
        return ""

    def _is_valid_city_token(self, token: str) -> bool:
        if len(token) < 3:
            return False
        if token in WEATHER_MARKERS or token in FILLER_WORDS:
            return False
        return token.isalpha()

    def _tokenize(self, query: str) -> list[dict[str, str]]:
        raw_tokens = re.findall(
            r"[A-Za-zÀ-ɏḀ-ỿ]+",
            query,
            re.UNICODE,
        )
        tokens: list[dict[str, str]] = []
        for raw_token in raw_tokens:
            display = self._strip_suffix_from_raw(raw_token)
            normalized = self._normalize_token(display)
            if not normalized:
                continue
            tokens.append(
                {
                    "raw": raw_token,
                    "display": display,
                    "normalized": normalized,
                }
            )
        return tokens

    def _strip_suffix_from_raw(self, raw_token: str) -> str:
        normalized = self._normalize_token(raw_token)
        for suffix in LOCATION_SUFFIXES:
            if normalized.endswith(suffix) and len(normalized) > len(suffix) + 2:
                return raw_token[: -len(suffix)]
        return raw_token

    def _normalize_token(self, value: str) -> str:
        lowered = value.lower().translate(TURKISH_CHAR_MAP)
        return "".join(character for character in lowered if character.isalpha())
