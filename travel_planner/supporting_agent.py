from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from . import prompt
from .tool import location_search, news_search

# The project's .env must win over any stale GOOGLE_API_KEY set system-wide.
load_dotenv(Path(__file__).parent / ".env", override=True)

# Free tier allows ~15 requests/min and one question makes several, so wait and retry on 429 instead of failing.
MODEL = Gemini(
    model="gemini-flash-lite-latest",
    retry_options=types.HttpRetryOptions(attempts=5, initial_delay=10, max_delay=60, http_status_codes=[429, 503]),
)


# shortcut: free-tier keys get no google_search grounding quota on Gemini 3, so this uses Google News RSS;
# once billing is on, swap tools to [google_search] (from google.adk.tools) for full web search.
google_search_agent = Agent(
    name="google_search_agent",
    model=MODEL,
    description="Searches Google for up-to-date information.",
    instruction=prompt.SEARCH_INSTRUCTION,
    tools=[FunctionTool(news_search)],
)

news_agent = Agent(
    name="news_agent",
    model=MODEL,
    description="Finds recent news, events and travel advisories for a destination.",
    instruction=prompt.NEWS_INSTRUCTION,
    tools=[AgentTool(agent=google_search_agent)],
)

places_agent = Agent(
    name="places_agent",
    model=MODEL,
    description="Finds real places to visit at a destination.",
    instruction=prompt.PLACES_INSTRUCTION,
    tools=[FunctionTool(location_search)],
)

travel_inspiration_agent = Agent(
    name="travel_inspiration_agent",
    model=MODEL,
    description="Inspires users with destination ideas, current news and places to visit.",
    instruction=prompt.INSPIRATION_INSTRUCTION,
    tools=[AgentTool(agent=news_agent), AgentTool(agent=places_agent)],
    disallow_transfer_to_peers=True,
)
