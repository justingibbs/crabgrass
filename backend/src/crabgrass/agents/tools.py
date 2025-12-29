"""Agent tools for the IdeaAssistant.

These functions are used by the agent to interact with the Crabgrass concepts.
Tools are plain functions with docstrings that describe their purpose and parameters.
"""

from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.summary import SummaryActions
from crabgrass.concepts.challenge import ChallengeActions
from crabgrass.concepts.approach import ApproachActions
from crabgrass.concepts.coherent_action import CoherentActionActions
from crabgrass.concepts.user import UserActions
from crabgrass.services.similarity import SimilarityService
from crabgrass.services.embedding import get_embedding_service


def save_idea(
    title: str,
    summary: str,
    challenge: str | None = None,
    approach: str | None = None,
    actions: list[str] | None = None,
    idea_id: str | None = None,
) -> dict:
    """Save or update an idea with its components.

    Creates a new idea or updates an existing one with the provided content.
    At minimum, a title and summary are required. Challenge, approach, and
    actions are optional.

    Args:
        title: The title of the idea (required)
        summary: A description of the idea (required)
        challenge: The problem or challenge being addressed (optional)
        approach: The guiding policy to address the challenge (optional)
        actions: List of specific action steps (optional)
        idea_id: If provided, updates the existing idea; otherwise creates new

    Returns:
        dict with status and the saved idea details
    """
    try:
        # Get current user for author_id
        current_user = UserActions.get_current()
        author_id = current_user.id

        if idea_id:
            # Update existing idea
            idea = IdeaActions.get_by_id(idea_id)
            if not idea:
                return {"status": "error", "error_message": f"Idea {idea_id} not found"}

            # Update title if changed
            if idea.title != title:
                IdeaActions.update(idea_id, title=title)

            # Update summary
            existing_summary = SummaryActions.get_by_idea_id(idea_id)
            if existing_summary:
                SummaryActions.update(existing_summary.id, content=summary)
            else:
                SummaryActions.create(idea_id, summary)

            # Update challenge
            existing_challenge = ChallengeActions.get_by_idea_id(idea_id)
            if challenge:
                if existing_challenge:
                    ChallengeActions.update(existing_challenge.id, content=challenge)
                else:
                    ChallengeActions.create(idea_id, challenge)
            elif existing_challenge:
                ChallengeActions.delete(existing_challenge.id)

            # Update approach
            existing_approach = ApproachActions.get_by_idea_id(idea_id)
            if approach:
                if existing_approach:
                    ApproachActions.update(existing_approach.id, content=approach)
                else:
                    ApproachActions.create(idea_id, approach)
            elif existing_approach:
                ApproachActions.delete(existing_approach.id)

            # Handle actions - for simplicity, we'll replace all actions
            if actions:
                # Delete existing actions
                existing_actions = CoherentActionActions.list_by_idea_id(idea_id)
                for action in existing_actions:
                    CoherentActionActions.delete(action.id)
                # Create new actions
                for action_content in actions:
                    CoherentActionActions.create(idea_id, action_content)

        else:
            # Create new idea
            idea = IdeaActions.create(title=title, author_id=author_id)
            idea_id = idea.id

            # Create summary
            SummaryActions.create(idea_id, summary)

            # Create challenge if provided
            if challenge:
                ChallengeActions.create(idea_id, challenge)

            # Create approach if provided
            if approach:
                ApproachActions.create(idea_id, approach)

            # Create actions if provided
            if actions:
                for action_content in actions:
                    CoherentActionActions.create(idea_id, action_content)

        return {
            "status": "success",
            "idea_id": idea_id,
            "title": title,
            "message": f"Idea '{title}' saved successfully",
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def find_similar(content: str, content_type: str = "summary", limit: int = 5) -> dict:
    """Find ideas with similar content.

    Searches for ideas that have similar content based on semantic similarity.
    This helps users discover related ideas and potential connections.

    Args:
        content: The text to find similarities for
        content_type: Type of content to search - "summary", "challenge", or "approach"
        limit: Maximum number of similar ideas to return (default 5)

    Returns:
        dict with status and list of similar ideas with titles and similarity scores
    """
    try:
        embedding_service = get_embedding_service()
        similarity_service = SimilarityService(embedding_service)

        # Generate embedding for the content
        embedding = embedding_service.embed(content)

        # Search based on content type
        if content_type == "summary":
            results = similarity_service.find_similar_summaries(embedding, limit=limit)
        elif content_type == "challenge":
            results = similarity_service.find_similar_challenges(embedding, limit=limit)
        elif content_type == "approach":
            results = similarity_service.find_similar_approaches(embedding, limit=limit)
        else:
            return {
                "status": "error",
                "error_message": f"Invalid content_type: {content_type}. Use 'summary', 'challenge', or 'approach'",
            }

        similar_ideas = [
            {
                "idea_id": r.idea_id,
                "title": r.title,
                "similarity_score": round(r.similarity, 3),
            }
            for r in results
        ]

        return {
            "status": "success",
            "similar_ideas": similar_ideas,
            "count": len(similar_ideas),
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def get_idea_context(idea_id: str) -> dict:
    """Get the current state of an idea being worked on.

    Retrieves all components of an idea including summary, challenge,
    approach, and actions. Useful for understanding what has been
    captured so far.

    Args:
        idea_id: The ID of the idea to retrieve

    Returns:
        dict with the idea's current state and all its components
    """
    try:
        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            return {"status": "error", "error_message": f"Idea {idea_id} not found"}

        # Get related components
        summary = SummaryActions.get_by_idea_id(idea_id)
        challenge = ChallengeActions.get_by_idea_id(idea_id)
        approach = ApproachActions.get_by_idea_id(idea_id)
        actions = CoherentActionActions.list_by_idea_id(idea_id)

        return {
            "status": "success",
            "idea": {
                "id": idea.id,
                "title": idea.title,
                "status": idea.status,
                "summary": summary.content if summary else None,
                "challenge": challenge.content if challenge else None,
                "approach": approach.content if approach else None,
                "actions": [
                    {"id": a.id, "content": a.content, "status": a.status}
                    for a in actions
                ],
            },
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}
