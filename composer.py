import logging
from google.adk.agents import Agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

instruction_prompt = """
You are an itinerary composer. Given a route and points of interest, write a clear, friendly and concise itinerary
for a tourist. Include times, locations, and helpful context.
"""

composer_agent = Agent(
    name="composer_agent",
    model="gemini-2.5-pro",
    description="Composes a readable travel itinerary from routing information.",
    instruction=instruction_prompt,
    tools=[]  # no tools needed for this agent
)
