from bot.services.weather_service import WeatherService


def get_weather(query: str, weather_service: WeatherService) -> str:
    return weather_service.get_weather(query)
