from bot.utils.logger import logger


TURKISH_CHAR_MAP = str.maketrans(
    {
        "\u00e7": "c",
        "\u011f": "g",
        "\u0131": "i",
        "\u00f6": "o",
        "\u015f": "s",
        "\u00fc": "u",
    }
)


class ToolPolicyEngine:
    def decide(self, user_message: str) -> dict[str, str] | None:
        normalized = self._normalize(user_message)
        logger.info(
            "ToolPolicy input: raw=%s normalized=%s",
            user_message,
            normalized,
        )

        if self._is_date_question(normalized):
            decision = {"tool": "date", "input": user_message}
            return self._log_decision("date", decision)

        if self._is_time_question(normalized):
            decision = {"tool": "clock", "input": user_message}
            return self._log_decision("time", decision)

        if self._is_weather_question(normalized):
            decision = {"tool": "weather", "input": user_message}
            return self._log_decision("weather", decision)

        if self._is_reminder_request(normalized):
            decision = {"tool": "reminder", "input": user_message}
            return self._log_decision("reminder", decision)

        if self._is_market_question(normalized):
            decision = {"tool": "search_web", "input": user_message}
            return self._log_decision("market", decision)

        if self._is_news_question(normalized):
            decision = {"tool": "search_web", "input": user_message}
            return self._log_decision("news", decision)

        logger.info("ToolPolicy matched rule: none")
        logger.info("ToolPolicy returned forced tool: None")
        return None

    def _normalize(self, value: str) -> str:
        lowered = value.lower().strip()
        translated = lowered.translate(TURKISH_CHAR_MAP)
        return " ".join(translated.split())

    def _log_decision(
        self,
        matched_rule: str,
        decision: dict[str, str],
    ) -> dict[str, str]:
        logger.info("ToolPolicy matched rule: %s", matched_rule)
        logger.info("ToolPolicy returned forced tool: %s", decision)
        return decision

    def _is_date_question(self, normalized: str) -> bool:
        date_keywords = (
            "today's date",
            "todays date",
            "what is the date",
            "current date",
            "bugun tarih",
            "bugunun tarihi",
            "tarih kac",
            "tarih ne",
            "hangi gun",
        )
        return any(keyword in normalized for keyword in date_keywords)

    def _is_time_question(self, normalized: str) -> bool:
        time_keywords = (
            "what time",
            "current time",
            "time is it",
            "saat kac",
            "su an saat",
            "simdi saat",
        )
        return any(keyword in normalized for keyword in time_keywords)

    def _is_market_question(self, normalized: str) -> bool:
        market_keywords = (
            "btc",
            "bitcoin",
            "usd",
            "eur",
            "gold",
            "altin",
            "stock",
            "stocks",
            "crypto",
            "exchange rate",
            "kur",
            "dolar",
            "euro",
            "borsa",
            "hisse",
        )
        return any(keyword in normalized for keyword in market_keywords)

    def _is_weather_question(self, normalized: str) -> bool:
        weather_keywords = (
            "weather",
            "forecast",
            "temperature",
            "hava nasil",
            "hava durumu",
            "kac derece",
            "derece",
            "sicaklik",
            "yagmur",
            "gunesli",
            "ruzgar",
        )
        return any(keyword in normalized for keyword in weather_keywords)

    def _is_news_question(self, normalized: str) -> bool:
        news_keywords = (
            "news",
            "headline",
            "headlines",
            "son haber",
            "haber",
            "gundem",
            "latest news",
            "breaking",
        )
        return any(keyword in normalized for keyword in news_keywords)

    def _is_reminder_request(self, normalized: str) -> bool:
        reminder_keywords = (
            "hatirlat",
            "remind me",
            "reminder",
        )
        return any(keyword in normalized for keyword in reminder_keywords)
