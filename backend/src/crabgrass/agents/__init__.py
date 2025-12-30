"""Agents package - AI agents for Crabgrass.

This package contains the AI agents that help users interact with the system.
Agents use the Concepts layer for persistence, ensuring signals fire and
sync handlers execute properly.

V2 adds background processing agents that consume from queues.
"""

from crabgrass.agents.idea_assistant import IdeaAssistantAgent, get_idea_assistant
from crabgrass.agents.state import IdeaContext
from crabgrass.agents.tools import save_idea, find_similar, propose_suggestion
from crabgrass.agents.runner import (
    BackgroundAgent,
    AgentOrchestrator,
    get_orchestrator,
)
from crabgrass.agents.background import (
    ConnectionAgent,
    NurtureAgent,
    SurfacingAgent,
    ObjectiveAgent,
)

__all__ = [
    # Human-facing agents
    "IdeaAssistantAgent",
    "get_idea_assistant",
    "IdeaContext",
    "save_idea",
    "find_similar",
    "propose_suggestion",
    # Background agent infrastructure
    "BackgroundAgent",
    "AgentOrchestrator",
    "get_orchestrator",
    # Background agents
    "ConnectionAgent",
    "NurtureAgent",
    "SurfacingAgent",
    "ObjectiveAgent",
]
