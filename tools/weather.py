import json
from urllib.request import Request, urlopen

from agent_framework import tool

from .geocoding import geocode_location


@tool
def get_weather(location: str) -> str:
    """Gets the weather for a given location."""
    try:
        place = geocode_location(location)
        if not place:
            return f"I could not find a location named {location}."

        forecast_url = (
            "https://api.open-meteo.com/v1/forecast?"
            f"latitude={place['latitude']}&longitude={place['longitude']}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
            "&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto"
        )
        with urlopen(Request(forecast_url, headers={"User-Agent": "llm-fun/1.0"}), timeout=10) as response:
            current = json.load(response)["current"]

        conditions = {
            0: "clear sky",
            1: "mainly clear",
            2: "partly cloudy",
            3: "overcast",
            45: "foggy",
            48: "depositing rime fog",
            51: "light drizzle",
            53: "moderate drizzle",
            55: "dense drizzle",
            61: "light rain",
            63: "moderate rain",
            65: "heavy rain",
            71: "light snow",
            73: "moderate snow",
            75: "heavy snow",
            80: "light rain showers",
            81: "moderate rain showers",
            82: "violent rain showers",
            95: "thunderstorm",
            96: "thunderstorm with light hail",
            99: "thunderstorm with heavy hail",
        }
        condition = conditions.get(current["weather_code"], "unknown conditions")
        place_name = ", ".join(filter(None, [place.get("name"), place.get("country")]))
        return (
            f"Current weather in {place_name}: {condition}, "
            f"{current['temperature_2m']}°F, feels like {current['apparent_temperature']}°F, "
            f"humidity {current['relative_humidity_2m']}%, wind {current['wind_speed_10m']} mph."
        )
    except Exception as error:
        return f"I could not retrieve weather for {location}: {error}"
