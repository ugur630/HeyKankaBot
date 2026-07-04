import json


class ResponseFormatter:
    def format_tool_response(
        self,
        tool_name: str,
        raw_output: str,
    ) -> str:
        parsed = self._parse_json(raw_output)

        if parsed is not None and "error" in parsed:
            return self.format_error_response(tool_name, parsed)

        if tool_name == "weather":
            return self.format_weather_response(parsed)

        if tool_name == "currency":
            return self.format_currency_response(parsed)

        if tool_name == "date":
            return self.format_date_response(parsed)

        if tool_name == "clock":
            return self.format_clock_response(parsed)

        if tool_name == "calculator":
            return self.format_calculator_response(parsed)

        if tool_name == "reminder":
            return self.format_reminder_response(parsed)

        if tool_name == "search_web":
            return self.format_search_response(parsed)

        return raw_output

    def format_weather_response(
        self,
        payload: dict[str, object] | None,
    ) -> str:
        if not payload:
            return "Kanka, hava durumunu su an alamadim."

        city = self._string_value(payload, "resolved_area") or self._string_value(
            payload, "city"
        ) or "Bu sehir"
        condition = self._string_value(payload, "condition")
        temperature = self._string_value(payload, "temperature_c")
        feels_like = self._string_value(payload, "feels_like_c")
        humidity = self._string_value(payload, "humidity")

        detail_lines: list[str] = [f"Kanka, su an {city}'de:"]
        if temperature:
            detail_lines.append(f"- Sicaklik: {temperature} C")
        if feels_like:
            detail_lines.append(f"- Hissedilen: {feels_like} C")
        if humidity:
            detail_lines.append(f"- Nem: %{humidity}")
        if condition:
            detail_lines.append(f"- Durum: {condition}")

        if len(detail_lines) == 1:
            return f"Kanka, {city} icin detayli hava bilgisi su an yok."

        return "\n".join(detail_lines)

    def format_currency_response(
        self,
        payload: dict[str, object] | None,
    ) -> str:
        if not payload:
            return "Kanka, kur bilgisini su an alamadim."

        from_code = self._string_value(payload, "from")
        to_code = self._string_value(payload, "to")
        rate = self._string_value(payload, "rate")
        date = self._string_value(payload, "date")

        if not (from_code and to_code and rate):
            return "Kanka, kur bilgisini su an alamadim."

        line = f"Kanka, 1 {from_code} = {rate} {to_code}"
        if date:
            line += f" ({date})"
        return line

    def format_search_response(
        self,
        payload: dict[str, object] | None,
    ) -> str:
        if not payload:
            return "Kanka, arama sonucunu su an toparlayamadim."

        results = payload.get("results")
        if not isinstance(results, list) or not results:
            return "Kanka, guvenilir bir sonuc bulamadim."

        lines = ["Kanka, en guvenilir adaylar sunlar:"]
        for result in results[:5]:
            if not isinstance(result, dict):
                continue
            title = str(result.get("title", "")).strip()
            url = str(result.get("url", "")).strip()
            snippet = str(result.get("snippet", "")).strip()
            if not title:
                continue
            line = f"- {title}"
            if snippet:
                line += f": {snippet}"
            if url:
                line += f" ({url})"
            lines.append(line)

        if len(lines) == 1:
            return "Kanka, guvenilir bir sonuc bulamadim."

        return "\n".join(lines)

    def format_reminder_response(
        self,
        payload: dict[str, object] | None,
    ) -> str:
        if not payload:
            return "Kanka, hatirlatmayi su an kaydedemedim."

        status = self._string_value(payload, "status")
        if status == "scheduled":
            message = self._string_value(payload, "message")
            remind_at = self._string_value(payload, "remind_at")
            recurrence = self._string_value(payload, "recurrence") or "none"
            lines = ["Kanka, hatirlatmayi kaydettim."]
            if message:
                lines.append(f"- Not: {message}")
            if remind_at:
                lines.append(f"- Zaman: {remind_at}")
            if recurrence and recurrence != "none":
                lines.append(f"- Tekrar: {recurrence}")
            return "\n".join(lines)

        if status == "due":
            message = self._string_value(payload, "message")
            remind_at = self._string_value(payload, "remind_at")
            lines = ["Kanka, hatirlatma zamani geldi."]
            if message:
                lines.append(f"- Not: {message}")
            if remind_at:
                lines.append(f"- Planlanan zaman: {remind_at}")
            return "\n".join(lines)

        return "Kanka, hatirlatmayi su an kaydedemedim."

    def format_date_response(
        self,
        payload: dict[str, object] | None,
    ) -> str:
        date = self._string_value(payload, "date")
        if not date:
            return "Kanka, bugunun tarihini su an alamadim."
        return f"Bugunun tarihi: {date}"

    def format_clock_response(
        self,
        payload: dict[str, object] | None,
    ) -> str:
        time = self._string_value(payload, "time")
        if not time:
            return "Kanka, saati su an alamadim."
        return f"Su an saat: {time}"

    def format_calculator_response(
        self,
        payload: dict[str, object] | None,
    ) -> str:
        if not payload:
            return "Kanka, hesabi su an yapamadim."

        expression = self._string_value(payload, "expression") or "ifade"
        result = self._string_value(payload, "result")
        if not result:
            return "Kanka, hesabi su an yapamadim."

        return f"{expression} = {result}"

    def format_error_response(
        self,
        tool_name: str,
        payload: dict[str, object],
    ) -> str:
        error_message = self._string_value(payload, "error")
        if tool_name in ("weather", "currency") and error_message:
            return f"Kanka, {error_message}"

        tool_messages = {
            "weather": "Kanka, hava durumunu su an alamadim.",
            "date": "Kanka, bugunun tarihini su an alamadim.",
            "clock": "Kanka, saati su an alamadim.",
            "calculator": "Kanka, hesabi su an yapamadim.",
            "reminder": "Kanka, hatirlatmayi su an kaydedemedim.",
            "search_web": "Kanka, aramayi su an tamamlayamadim.",
            "currency": "Kanka, kur bilgisini su an alamadim.",
        }
        return tool_messages.get(
            tool_name,
            "Kanka, bu bilgiyi su an alamadim.",
        )

    def _parse_json(self, raw_output: str) -> dict[str, object] | None:
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        return parsed

    def _string_value(
        self,
        payload: dict[str, object] | None,
        key: str,
    ) -> str:
        if not payload or key not in payload:
            return ""
        value = payload.get(key)
        if value is None:
            return ""
        return str(value)
