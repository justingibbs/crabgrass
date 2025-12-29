"""Agents package - AI agents for Crabgrass.

Contains the IdeaAssistant agent and its tools.
"""

from crabgrass.agents.idea_assistant import (
    create_idea_assistant_agent,
    get_idea_assistant_agent,
)
from crabgrass.agents.tools import save_idea, find_similar, get_idea_context

__all__ = [
    "create_idea_assistant_agent",
    "get_idea_assistant_agent",
    "save_idea",
    "find_similar",
    "get_idea_context",
]
