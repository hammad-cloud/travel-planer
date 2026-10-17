from google.adk.agents import Agent

from .supporting_agent import MODEL, travel_inspiration_agent

root_agent = Agent(
    name="travel_planner",
    model=MODEL,
    description="Main travel planning assistant.",
    instruction=(
        "You are a friendly travel planner. Greet the user and learn their trip basics "
        "(where, when, budget, interests). For destination ideas, news or places to visit, "
        "transfer to travel_inspiration_agent."
    ),
    sub_agents=[travel_inspiration_agent],
)
