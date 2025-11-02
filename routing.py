import os
import logging
from dotenv import load_dotenv

from google.adk.agents import Agent
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TransportProtocol
from google.adk.tools import google_maps_grounding
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from agent_a2a_server import create_agent_a2a_server

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from logging_ring import RingBufferHandler, attach_log_api

instruction_prompt = """
    You are a routing agent. Use the google_maps_grounding tool to estimate the best route and travel times 
    between a start and destination with optional waypoints.
    You can use the tool: google_maps_grounding.
    Walking is preferable but local transportation is also acceptable, if available.
"""

routing_agent = Agent(
    name="routing_agent",
    model="gemini-2.5-pro",
    description=(
        "Estimates an optimal travel route using ADK v1.15+ google_maps_grounding tool."
    ),
    tools=[google_maps_grounding],
)

routing_agent_card = AgentCard(
    name='Routing Agent',
    url='http://localhost:10021',
    description='Uses Google Maps to estimate the best route and travel times.',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='routing_agent',
            name='Routing Agent',
            description='Uses Google Maps to estimate the best route and travel times',
            tags=['locations', 'routes', 'traffic', 'distances'],
            examples=[
                "How to get from place A to place B?",
                'Show me the best route from A to B',
                'Is there a train from A to B?',
                'How crowded is street A at the hour H?'
            ],
        )
    ],
)

remote_routing_agent = RemoteA2aAgent(
    name='routing_agent',
    description='Uses Google Maps to estimate the best route and travel times.',
    agent_card=f'http://localhost:10021{AGENT_CARD_WELL_KNOWN_PATH}',
)


a2a_app = create_agent_a2a_server(
    agent=routing_agent,
    agent_card=routing_agent_card
)
application = a2a_app.build()  # <- ASGI app

rbh = RingBufferHandler(maxlen=2000, service=os.getenv("AGENT_NAME", "root_agent"))
logging.getLogger().addHandler(rbh)
logging.getLogger().setLevel(logging.INFO)  # or DEBUG
attach_log_api(application, rbh)

def main():
    import uvicorn
    uvicorn.run(
        "routing:application",  # module:var
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "10021")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )

if __name__ == "__main__":
    main()