import json
import os
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from agent_framework import tool


@tool
def search_wikipedia(topic: str, max_results: int = 5) -> str:
    """Searches English Wikipedia and returns matching article titles and URLs."""
    if not topic.strip():
        return "Provide a topic to search for."

    count = max(1, min(max_results, 10))
    query = urlencode(
        {
            "action": "query",
            "format": "json",
            "list": "search",
            "srnamespace": 0,
            "srsearch": topic,
            "srlimit": count,
            "utf8": 1,
        }
    )
    request = Request(
        f"https://en.wikipedia.org/w/api.php?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": os.environ.get(
                "WIKIPEDIA_API_USER_AGENT",
                "llm-fun/1.0 (Wikipedia article link search)",
            ),
        },
    )

    try:
        with urlopen(request, timeout=10) as response:
            results = json.load(response).get("query", {}).get("search", [])
    except Exception as error:
        return f"Wikipedia search failed: {error}"

    if not results:
        return f"No Wikipedia articles found for {topic}."

    return "\n\n".join(
        f"{index}. {result['title']}\n"
        f"https://en.wikipedia.org/wiki/{quote(result['title'].replace(' ', '_'), safe='()_,-')}"
        for index, result in enumerate(results[:count], start=1)
    )