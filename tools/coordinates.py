from agent_framework import tool

from .geocoding import geocode_location


@tool
def get_coordinates(location: str) -> str:
    """Finds the latitude and longitude for a named location."""
    try:
        place = geocode_location(location)
        if not place:
            return f"I could not find a location named {location}."

        place_name = ", ".join(filter(None, [place.get("name"), place.get("country")]))
        return f"{place_name}: latitude {place['latitude']}, longitude {place['longitude']}."
    except Exception as error:
        return f"I could not find coordinates for {location}: {error}"
