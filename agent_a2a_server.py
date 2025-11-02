import logging

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from dotenv import load_dotenv
from google.adk.a2a.executor.a2a_agent_executor import (
    A2aAgentExecutor,
    A2aAgentExecutorConfig,
)
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def create_agent_a2a_server(agent, agent_card):
    """Create an A2A server for any ADK agent.

    Args:
        agent: The ADK agent instance
        agent_card: The ADK agent card

    Returns:
        A2AStarletteApplication instance
    """
    runner = Runner(
        app_name=agent.name,
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    config = A2aAgentExecutorConfig()
    executor = A2aAgentExecutor(runner=runner, config=config)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A application
    return A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
