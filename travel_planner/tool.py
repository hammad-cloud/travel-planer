import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from geopy.exc import GeopyError
from geopy.geocoders import Nominatim

# Nominatim's usage policy requires a unique user agent.
geolocator = Nominatim(user_agent="travel-planner-adk", timeout=10)


def location_search(query: str, limit: int = 5) -> dict:
    """Finds real places (attractions, restaurants, hotels, landmarks) matching a query.

    Args:
        query: What to look for, e.g. "museums in Lisbon" or "beaches near Bali".
        limit: Max number of places to return.

    Returns:
        A dict with a list of places, each with name, address, type, lat and lon.
    """
    # shortcut: free OpenStreetMap Nominatim (1 req/sec, no ratings); swap for Google Places API if you need reviews/photos.
    try:
        results = geolocator.geocode(query, exactly_one=False, limit=limit) or []
    except GeopyError as e:
        return {"status": "error", "message": str(e)}
    return {
        "status": "success",
        "places": [
            {
                "name": r.raw.get("name") or r.address.split(",")[0],
                "address": r.address,
                "type": r.raw.get("type"),
                "lat": r.latitude,
                "lon": r.longitude,
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
