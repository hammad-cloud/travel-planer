import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

# Free tier allows ~15 requests/min and one question makes several, so wait and retry on 429 instead of failing.
MODEL = Gemini(
    model="gemini-flash-lite-latest",
    retry_options=types.HttpRetryOptions(attempts=5, initial_delay=10, max_delay=60, http_status_codes=[429, 503]),
)


def location_search(query: str, limit: int = 5) -> dict:
    """Finds real places (attractions, restaurants, hotels, landmarks) matching a query.

    Args:
        query: What to look for, e.g. "museums in Lisbon" or "beaches near Bali".
        limit: Max number of places to return.

    Returns:
        A dict with a list of places, each with name, address, type, lat and lon.
    """
    # shortcut: free OpenStreetMap Nominatim (1 req/sec, no ratings); swap for Google Places API if you need reviews/photos.
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": limit}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "travel-planner-adk/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.load(resp)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {
        "status": "success",
        "places": [
            {
                "name": r.get("name") or r["display_name"].split(",")[0],
                "address": r["display_name"],
                "type": r.get("type"),
                "lat": r["lat"],
                "lon": r["lon"],
            }
            for r in results
        ],
    }


def news_search(query: str, limit: int = 8) -> dict:
    """Searches Google News for recent articles.

    Args:
        query: What to search, e.g. "Lisbon festival" or "Bali travel advisory".
        limit: Max number of articles to return.

    Returns:
        A dict with a list of articles, each with title, source, date and link.
    """
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": "en", "gl": "US", "ceid": "US:en"})
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            items = ET.parse(resp).getroot().iter("item")
            articles = [
                {"title": i.findtext("title"), "source": i.findtext("source"), "date": i.findtext("pubDate"), "link": i.findtext("link")}
                for _, i in zip(range(limit), items)
            ]
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "articles": articles}


# shortcut: free-tier keys get no google_search grounding quota on Gemini 3, so this uses Google News RSS;
# once billing is on, swap tools to [google_search] (from google.adk.tools) for full web search.
google_search_agent = Agent(
    name="google_search_agent",
    model=MODEL,
    description="Searches Google for up-to-date information.",
    instruction="Answer the request using the news_search tool. Be concise and include sources.",
    tools=[FunctionTool(news_search)],
)

news_agent = Agent(
    name="news_agent",
    model=MODEL,
    description="Finds recent news, events and travel advisories for a destination.",
    instruction=(
        "Find current news relevant to a traveller for the given destination: events, festivals, "
        "weather issues, strikes, safety advisories. Use the google_search_agent tool. "
        "Return a short bulleted list with dates."
    ),
    tools=[AgentTool(agent=google_search_agent)],
)

places_agent = Agent(
    name="places_agent",
    model=MODEL,
    description="Finds real places to visit at a destination.",
    instruction=(
        "Suggest places to visit for the given destination and interests. Use the location_search "
        "tool with specific queries (e.g. 'museums in Rome'). Return name, address and why it's worth it."
    ),
    tools=[FunctionTool(location_search)],
)

travel_inspiration_agent = Agent(
    name="travel_inspiration_agent",
    model=MODEL,
    description="Inspires users with destination ideas, current news and places to visit.",
    instruction=(
        "Help the user pick and get excited about a destination. If they have none, suggest a few "
        "based on their preferences. For a chosen destination, call news_agent for what's happening "
        "now and places_agent for things to see, then combine both into one inspiring summary."
    ),
    tools=[AgentTool(agent=news_agent), AgentTool(agent=places_agent)],
)
