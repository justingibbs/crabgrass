"""Agents package - AI agents for Crabgrass.

This package contains the AI agents that help users interact with the system.
Agents use the Concepts layer for persistence, ensuring signals fire and
sync handlers execute properly.
"""

from crabgrass.agents.idea_assistant import IdeaAssistantAgent, get_idea_assistant
from crabgrass.agents.state import IdeaContext
from crabgrass.agents.tools import save_idea, find_similar

__all__ = [
    "IdeaAssistantAgent",
    "get_idea_assistant",
    "IdeaContext",
    "save_idea",
    "find_similar",
]
