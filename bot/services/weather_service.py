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
        "\u00e7": "c",
        "\u011f": "g",
        "\u0131": "i",
        "\u00f6": "o",
        "\u015f": "s",
        "\u00fc": "u",
        "\u0130": "I",
    }
)


class WeatherService:
    def __init__(
        self,
        default_city: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.default_city = default_city.strip() if default_city else None
        self.timeout_seconds = timeout_seconds

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

        url = f"https://wttr.in/{quote_plus(city)}?format=j1"
        logger.info("Weather URL: %s", url)

        started_at = time.perf_counter()
        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=self.timeout_seconds,
                headers={"User-Agent": "HeyKankaBot/0.7"},
            ) as client:
                response = client.get(url)
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                logger.info("HTTP Status: %s", response.status_code)
                logger.info("Weather response time: %.2f ms", elapsed_ms)
                logger.info(
                    "Weather response body (first 300 chars): %s",
                    response.text[:300],
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return json.dumps(
                {
                    "error": (
                        "Weather information could not be retrieved: "
                        f"{exc}"
                    ),
                }
            )

        try:
            payload = response.json()
        except ValueError:
            return json.dumps(
                {
                    "error": "Weather service returned invalid data.",
                }
            )

        current = (payload.get("current_condition") or [{}])[0]
        area = (payload.get("nearest_area") or [{}])[0]
        weather_desc = (current.get("weatherDesc") or [{}])[0]

        result = {
            "city": city,
            "resolved_area": area.get("areaName", [{}])[0].get(
                "value", city
            ),
            "temperature_c": current.get("temp_C"),
            "feels_like_c": current.get("FeelsLikeC"),
            "humidity": current.get("humidity"),
            "condition": weather_desc.get("value"),
            "observation_time_utc": current.get("observation_time"),
            "source": "wttr.in",
        }

        return json.dumps(result)

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
            r"[A-Za-z\u00c0-\u024f\u1e00-\u1eff]+",
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
