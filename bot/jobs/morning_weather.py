from bot.jobs import BaseJob, JobContext


class MorningWeatherJob(BaseJob):
    name = "morning_weather"

    def __init__(self, context: JobContext) -> None:
        super().__init__(
            context,
            enabled=context.settings.feature_morning_weather_enabled,
        )

    def run(self) -> None:
        chat_id = self.context.settings.default_chat_id
        if chat_id is None:
            raise ValueError("DEFAULT_CHAT_ID is not configured.")

        city = self.context.settings.default_city
        if not city:
            raise ValueError("DEFAULT_CITY is not configured.")

        raw_output = self.context.weather_service.get_weather(city)
        formatted_message = self.context.response_formatter.format_tool_response(
            tool_name="weather",
            raw_output=raw_output,
        )
        final_message = self._build_message(formatted_message)
        self.context.telegram_sender.send_text(chat_id, final_message)

    def _build_message(self, weather_message: str) -> str:
        return "Gunaydin!\n\n" + weather_message

    def build_optional_ai_comment_prompt(self) -> str:
        return (
            "Future extension point for an optional AI-generated comment "
            "based on already formatted deterministic weather data."
        )
