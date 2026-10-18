from google.adk.agents import Agent

from . import prompt
from .supporting_agent import MODEL, travel_inspiration_agent

root_agent = Agent(
    name="travel_planner",
    model=MODEL,
    description="Main travel planning assistant.",
    instruction=prompt.ROOT_INSTRUCTION,
    sub_agents=[travel_inspiration_agent],
)
