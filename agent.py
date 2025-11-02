import os
import logging
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TransportProtocol


from agent_a2a_server import create_agent_a2a_server
from composer import composer_agent
from discovery import remote_discovery_agent
from routing import remote_routing_agent

from logging_ring import RingBufferHandler, attach_log_api

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

load_dotenv()


instruction_prompt = """
You are a travel coordinator agent that creates a personalized itinerary for a traveler based on their interests and available time.
Ypu have access to three Agent Tools:
    - discovery_agent
    - routing_agent
    - composer_agent

- Use `discovery_agent` to find relevant places. 
    This would be the first action typically.
- Use `routing_agent` to plan the optimal route between those places.
    Use this tool once you decided on a number of places to visit.
- Use `composer_agent` to convert the raw route and POIs into a clear, human-readable itinerary. 
    Use preferably markdown notation.
- Do not ask user for further clarifications. Just propose the attractions, route, adding 
hour information and distances, if you have these informations.
- Allways offer one option for the local exploration, do not create a conversational experience.
- Do not ask the user for confirmation before calling the tools.

"""

root_agent = Agent(
    name="local_explorer_assistant",
    model="gemini-2.5-pro",
    description="Coordinates discovery, routing, and itinerary composition to plan a smart local day trip.",
    instruction=instruction_prompt,
    tools=[
        AgentTool(agent=remote_discovery_agent),
        AgentTool(agent=remote_routing_agent),
        AgentTool(agent=composer_agent)
    ]
)

root_agent_card = AgentCard(
    name='Trend Analysis Host',
    url='http://localhost:10022',
    description='Coordinates discovery, routing, and itinerary composition to plan a smart local day trip.',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['application/json'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='local_explorer_assistant',
            name='Local Explorer Assistant',
            description='Coordinates discovery, routing, and itinerary composition to plan a smart local day trip.',
            tags=['landmarks', 'attractions', 'museums', 'gardens', 'street art', 'street music', 'street food', 'views'],
            examples=[
                'What I can see in the city in 3h?',
                "I love art and street food. I do not like crowded places. What I can see in 2h?",
                'I like museums and quiet gardens. I have half a day.',
            ],
        )
    ],
)


a2a_app = create_agent_a2a_server(
    agent=root_agent,
    agent_card=root_agent_card
)
application = a2a_app.build()  # <- ASGI app

rbh = RingBufferHandler(maxlen=2000, service=os.getenv("AGENT_NAME", "root_agent"))
logging.getLogger().addHandler(rbh)
logging.getLogger().setLevel(logging.INFO)  # or DEBUG
attach_log_api(application, rbh)

def main():
    import uvicorn
    uvicorn.run(
        "agent:application",  # module:var
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "10022")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )

if __name__ == "__main__":
    main()