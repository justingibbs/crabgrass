"""Tool implementations for the IdeaAssistant agent.

These tools call concept actions directly, which ensures signals fire
and sync handlers execute (e.g., embedding generation).
"""

import logging
from dataclasses import dataclass, field

from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.summary import SummaryActions
from crabgrass.concepts.challenge import ChallengeActions
from crabgrass.concepts.approach import ApproachActions
from crabgrass.concepts.coherent_action import CoherentActionActions
from crabgrass.concepts.user import UserActions
from crabgrass.services.similarity import SimilarityService
from crabgrass.services.embedding import get_embedding_service

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Result Types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SaveIdeaResult:
    """Result of save_idea tool."""

    success: bool
    idea_id: str
    message: str
    created_new: bool = False


@dataclass
class SimilarIdeaInfo:
    """A single similar idea in find_similar results."""

    idea_id: str
    title: str
    similarity: float


@dataclass
class FindSimilarResult:
    """Result of find_similar tool."""

    success: bool
    similar_ideas: list[SimilarIdeaInfo] = field(default_factory=list)
    message: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Tool Functions
# ─────────────────────────────────────────────────────────────────────────────


def save_idea(
    title: str,
    summary: str = "",
    challenge: str = "",
    approach: str = "",
    idea_id: str = "",
) -> dict:
    """Save or update an idea.

    Creates a new idea if idea_id is not provided, otherwise updates existing.
    Only provided fields will be saved/updated.

    Args:
        title: The idea title (required for new ideas).
        summary: Optional summary/description of the idea.
        challenge: Optional challenge statement (the problem being addressed).
        approach: Optional approach/strategy (guiding policy).
        idea_id: If provided, updates existing idea; otherwise creates new.

    Returns:
        Dictionary with success status, idea_id, and message.
    """
    try:
        current_user = UserActions.get_current()
        created_new = False

        if idea_id and idea_id.strip():
            # Update existing idea
            idea = IdeaActions.get_by_id(idea_id)
            if not idea:
                return {
                    "success": False,
                    "idea_id": "",
                    "message": f"Idea {idea_id} not found",
                    "created_new": False,
                }

            # Update title if changed
            if title and title != idea.title:
                IdeaActions.update(idea_id, title=title)
        else:
            # Create new idea
            if not title:
                return {
                    "success": False,
                    "idea_id": "",
                    "message": "Title is required for new ideas",
                    "created_new": False,
                }
            idea = IdeaActions.create(title=title, author_id=current_user.id)
            idea_id = idea.id
            created_new = True
            logger.info(f"Created new idea: {idea_id}")

        # Handle Summary (one per idea)
        if summary and summary.strip():
            existing_summary = SummaryActions.get_by_idea_id(idea_id)
            if existing_summary:
                SummaryActions.update(existing_summary.id, content=summary)
                logger.info(f"Updated summary for idea {idea_id}")
            else:
                SummaryActions.create(idea_id=idea_id, content=summary)
                logger.info(f"Created summary for idea {idea_id}")

        # Handle Challenge (one per idea)
        if challenge and challenge.strip():
            existing_challenge = ChallengeActions.get_by_idea_id(idea_id)
            if existing_challenge:
                ChallengeActions.update(existing_challenge.id, content=challenge)
                logger.info(f"Updated challenge for idea {idea_id}")
            else:
                ChallengeActions.create(idea_id=idea_id, content=challenge)
                logger.info(f"Created challenge for idea {idea_id}")

        # Handle Approach (one per idea)
        if approach and approach.strip():
            existing_approach = ApproachActions.get_by_idea_id(idea_id)
            if existing_approach:
                ApproachActions.update(existing_approach.id, content=approach)
                logger.info(f"Updated approach for idea {idea_id}")
            else:
                ApproachActions.create(idea_id=idea_id, content=approach)
                logger.info(f"Created approach for idea {idea_id}")

        action_word = "Created" if created_new else "Updated"
        return {
            "success": True,
            "idea_id": idea_id,
            "message": f"{action_word} idea successfully",
            "created_new": created_new,
        }

    except Exception as e:
        logger.error(f"Error saving idea: {e}", exc_info=True)
        return {
            "success": False,
            "idea_id": idea_id or "",
            "message": f"Error saving idea: {str(e)}",
            "created_new": False,
        }


def find_similar(
    content: str,
    limit: int = 5,
    exclude_idea_id: str = "",
) -> dict:
    """Find ideas similar to the given content.

    Uses semantic similarity to find related ideas in the database.

    Args:
        content: The text content to find similar ideas for.
        limit: Maximum number of results (default 5, max 20).
        exclude_idea_id: Optional idea ID to exclude from results.

    Returns:
        Dictionary with success status and list of similar ideas.
    """
    try:
        if not content or not content.strip():
            return {
                "success": False,
                "similar_ideas": [],
                "message": "Content is required to find similar ideas",
            }

        # Clamp limit
        limit = min(max(1, limit), 20)

        # Generate embedding for the content
        embedding_service = get_embedding_service()
        embedding = embedding_service.embed(content)

        # Find similar summaries
        similarity_service = SimilarityService()
        similar = similarity_service.find_similar_summaries(
            embedding=embedding,
            limit=limit,
            exclude_idea_id=exclude_idea_id if exclude_idea_id else None,
        )

        similar_ideas = [
            {
                "idea_id": s.idea_id,
                "title": s.title,
                "similarity": round(s.similarity, 3),
            }
            for s in similar
        ]

        return {
            "success": True,
            "similar_ideas": similar_ideas,
            "message": f"Found {len(similar)} similar ideas",
        }

    except Exception as e:
        logger.error(f"Error finding similar ideas: {e}", exc_info=True)
        return {
            "success": False,
            "similar_ideas": [],
            "message": f"Error finding similar ideas: {str(e)}",
        }


def propose_suggestion(
    idea_id: str,
    field: str,
    content: str,
    reason: str = "",
) -> dict:
    """Propose a suggestion for an idea field without immediately saving it.

    Use this tool when you want to suggest content for the user to review
    before accepting. The suggestion will be shown to the user for approval.

    Args:
        idea_id: The ID of the idea this suggestion is for.
        field: The field to suggest content for ("summary", "challenge", or "approach").
        content: The suggested content.
        reason: Optional explanation of why this content is being suggested.

    Returns:
        Dictionary with success status, suggestion_id, and the suggestion details.
    """
    import uuid

    try:
        if not idea_id or not idea_id.strip():
            return {
                "success": False,
                "message": "idea_id is required",
            }

        valid_fields = ["summary", "challenge", "approach"]
        if field not in valid_fields:
            return {
                "success": False,
                "message": f"field must be one of: {', '.join(valid_fields)}",
            }

        if not content or not content.strip():
            return {
                "success": False,
                "message": "content is required",
            }

        # Verify idea exists
        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            return {
                "success": False,
                "message": f"Idea {idea_id} not found",
            }

        # Generate a unique suggestion ID
        suggestion_id = f"sug-{uuid.uuid4().hex[:8]}"

        logger.info(f"Proposed suggestion {suggestion_id} for {field} on idea {idea_id}")

        return {
            "success": True,
            "suggestion_id": suggestion_id,
            "idea_id": idea_id,
            "field": field,
            "content": content.strip(),
            "reason": reason.strip() if reason else "",
            "message": f"Suggestion proposed for {field}",
        }

    except Exception as e:
        logger.error(f"Error proposing suggestion: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error proposing suggestion: {str(e)}",
        }


def add_action(
    idea_id: str,
    action: str,
) -> dict:
    """Add a coherent action to an existing idea.

    Args:
        idea_id: The ID of the idea to add the action to.
        action: The action item content.

    Returns:
        Dictionary with success status and message.
    """
    try:
        if not idea_id or not idea_id.strip():
            return {
                "success": False,
                "message": "idea_id is required",
            }

        if not action or not action.strip():
            return {
                "success": False,
                "message": "action content is required",
            }

        # Verify idea exists
        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            return {
                "success": False,
                "message": f"Idea {idea_id} not found",
            }

        # Create the action
        CoherentActionActions.create(idea_id=idea_id, content=action.strip())
        logger.info(f"Added action to idea {idea_id}")

        return {
            "success": True,
            "message": "Action added successfully",
        }

    except Exception as e:
        logger.error(f"Error adding action: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error adding action: {str(e)}",
        }
