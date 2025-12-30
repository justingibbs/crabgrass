"""State model for the IdeaAssistant agent.

Tracks the current state of an idea being developed through conversation.
"""

from dataclasses import dataclass, field
from typing import Literal


# Stage in the idea development flow
IdeaStage = Literal["initial", "summary", "challenge", "approach", "actions", "complete"]


@dataclass
class IdeaContext:
    """Current state of the idea being developed.

    This context is passed to the agent with each message and updated
    as the agent helps the user structure their idea.
    """

    idea_id: str | None = None
    title: str | None = None
    summary: str | None = None
    challenge: str | None = None
    approach: str | None = None
    coherent_actions: list[str] = field(default_factory=list)

    # Tracking stage in the idea development flow
    stage: IdeaStage = "initial"

    def to_context_string(self) -> str:
        """Format the current state for the agent's system prompt."""
        parts = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.summary:
            parts.append(f"Summary: {self.summary}")
        if self.challenge:
            parts.append(f"Challenge: {self.challenge}")
        if self.approach:
            parts.append(f"Approach: {self.approach}")
        if self.coherent_actions:
            actions_str = "\n".join(f"  - {a}" for a in self.coherent_actions)
            parts.append(f"Coherent Actions:\n{actions_str}")

        if not parts:
            return "No idea captured yet."
        return "\n".join(parts)

    def to_dict(self) -> dict:
        """Convert to dictionary for AG-UI state snapshot events."""
        return {
            "idea_id": self.idea_id,
            "title": self.title,
            "summary": self.summary,
            "challenge": self.challenge,
            "approach": self.approach,
            "coherent_actions": self.coherent_actions,
            "stage": self.stage,
        }
