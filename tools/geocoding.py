import json
from urllib.parse import quote
from urllib.request import Request, urlopen


def geocode_location(location: str) -> dict | None:
    geocode_url = (
        "https://geocoding-api.open-meteo.com/v1/search?name="
        f"{quote(location)}&count=1&language=en&format=json"
    )
    with urlopen(Request(geocode_url, headers={"User-Agent": "llm-fun/1.0"}), timeout=10) as response:
        places = json.load(response).get("results", [])
    return places[0] if places else None
