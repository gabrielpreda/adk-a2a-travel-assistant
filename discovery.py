import os
import logging
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.tools import google_search
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TransportProtocol
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from agent_a2a_server import create_agent_a2a_server

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from logging_ring import RingBufferHandler, attach_log_api

instruction_prompt = """
You are a travel discovery agent. Use Google Search to find the most relevant places and activities for a tourist,
based on given location and interests. Return a short list or paragraph.
Note: this list will be used further by the routing Agent.
"""

discovery_agent = Agent(
    name="discovery_agent",
    model="gemini-2.5-pro",
    description="Uses Google Search to discover relevant places.",
    instruction=instruction_prompt,
    tools=[google_search]
)


discovery_agent_card = AgentCard(
    name='Discovery Agent',
    url='http://localhost:10020',
    description='Uses Google Search to discover relevant places.',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='discovery_agent',
            name='Discovery Agent',
            description='Uses Google Search to discover relevant places',
            tags=['locations', 'landmarks', 'great views', 'historical places'],
            examples=[
                "What to view in this town?",
                'Show me the best places around',
                'What is the most famous places in this area?',
                'What museums are most visited around here?'
            ],
        )
    ],
)

remote_discovery_agent = RemoteA2aAgent(
    name='discover_places',
    description='Uses Google Search to discover relevant places.',
    agent_card=f'http://localhost:10020{AGENT_CARD_WELL_KNOWN_PATH}',
)


a2a_app = create_agent_a2a_server(
    agent=discovery_agent,
    agent_card=discovery_agent_card
)
application = a2a_app.build()  # <- ASGI app

rbh = RingBufferHandler(maxlen=2000, service=os.getenv("AGENT_NAME", "root_agent"))
logging.getLogger().addHandler(rbh)
logging.getLogger().setLevel(logging.INFO)  # or DEBUG
attach_log_api(application, rbh)

def main():
    import uvicorn
    uvicorn.run(
        "discovery:application",  # module:var
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "10020")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )

if __name__ == "__main__":
    main()
