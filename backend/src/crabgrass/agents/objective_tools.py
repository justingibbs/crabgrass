"""Tool implementations for the ObjectiveAssistant agent.

These tools call concept actions directly, which ensures signals fire
and sync handlers execute (e.g., embedding generation).
"""

import logging
from dataclasses import dataclass, field

from crabgrass.concepts.objective import ObjectiveActions
from crabgrass.concepts.user import UserActions
from crabgrass.services.similarity import SimilarityService
from crabgrass.services.embedding import get_embedding_service

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Tool Functions
# ─────────────────────────────────────────────────────────────────────────────


def save_objective(
    title: str,
    description: str,
    parent_id: str = "",
    objective_id: str = "",
) -> dict:
    """Save or update an objective.

    Creates a new objective if objective_id is not provided, otherwise updates existing.
    Only provided fields will be saved/updated.

    Args:
        title: The objective title (required for new objectives).
        description: The objective description (required for new objectives).
        parent_id: Optional parent objective ID for hierarchy.
        objective_id: If provided, updates existing objective; otherwise creates new.

    Returns:
        Dictionary with success status, objective_id, and message.
    """
    try:
        current_user = UserActions.get_current()
        created_new = False

        if objective_id and objective_id.strip():
            # Update existing objective
            objective = ObjectiveActions.get_by_id(objective_id)
            if not objective:
                return {
                    "success": False,
                    "objective_id": "",
                    "message": f"Objective {objective_id} not found",
                    "created_new": False,
                }

            # Prepare update fields
            update_kwargs = {}
            if title and title != objective.title:
                update_kwargs["title"] = title
            if description and description != objective.description:
                update_kwargs["description"] = description
            if parent_id is not None:  # Allow clearing parent_id
                update_kwargs["parent_id"] = parent_id if parent_id.strip() else None

            if update_kwargs:
                ObjectiveActions.update(objective_id, **update_kwargs)
                logger.info(f"Updated objective: {objective_id}")

        else:
            # Create new objective
            if not title:
                return {
                    "success": False,
                    "objective_id": "",
                    "message": "Title is required for new objectives",
                    "created_new": False,
                }
            if not description:
                return {
                    "success": False,
                    "objective_id": "",
                    "message": "Description is required for new objectives",
                    "created_new": False,
                }

            objective = ObjectiveActions.create(
                title=title,
                description=description,
                author_id=current_user.id,
                parent_id=parent_id if parent_id and parent_id.strip() else None,
            )
            objective_id = objective.id
            created_new = True
            logger.info(f"Created new objective: {objective_id}")

        action_word = "Created" if created_new else "Updated"
        return {
            "success": True,
            "objective_id": objective_id,
            "message": f"{action_word} objective successfully",
            "created_new": created_new,
        }

    except Exception as e:
        logger.error(f"Error saving objective: {e}", exc_info=True)
        return {
            "success": False,
            "objective_id": objective_id or "",
            "message": f"Error saving objective: {str(e)}",
            "created_new": False,
        }


def list_objectives(
    status: str = "Active",
    limit: int = 20,
) -> dict:
    """List all objectives with optional status filter.

    Args:
        status: Filter by status ("Active" or "Retired"). Default is "Active".
        limit: Maximum number of results (default 20, max 50).

    Returns:
        Dictionary with success status and list of objectives.
    """
    try:
        # Validate status
        if status not in ("Active", "Retired"):
            status = "Active"

        # Clamp limit
        limit = min(max(1, limit), 50)

        # Get objectives
        objectives = ObjectiveActions.list_all(status=status)

        # Limit results
        objectives = objectives[:limit]

        objective_list = [
            {
                "objective_id": o.id,
                "title": o.title,
                "description": o.description[:200] + "..." if len(o.description) > 200 else o.description,
                "parent_id": o.parent_id,
                "status": o.status,
            }
            for o in objectives
        ]

        return {
            "success": True,
            "objectives": objective_list,
            "count": len(objective_list),
            "message": f"Found {len(objective_list)} {status.lower()} objectives",
        }

    except Exception as e:
        logger.error(f"Error listing objectives: {e}", exc_info=True)
        return {
            "success": False,
            "objectives": [],
            "count": 0,
            "message": f"Error listing objectives: {str(e)}",
        }


def find_similar_objectives(
    description: str,
    limit: int = 5,
    exclude_objective_id: str = "",
) -> dict:
    """Find objectives with similar descriptions.

    Uses semantic similarity to find related objectives in the database.

    Args:
        description: The text content to find similar objectives for.
        limit: Maximum number of results (default 5, max 20).
        exclude_objective_id: Optional objective ID to exclude from results.

    Returns:
        Dictionary with success status and list of similar objectives.
    """
    try:
        if not description or not description.strip():
            return {
                "success": False,
                "similar_objectives": [],
                "message": "Description is required to find similar objectives",
            }

        # Clamp limit
        limit = min(max(1, limit), 20)

        # Generate embedding for the description
        embedding_service = get_embedding_service()
        embedding = embedding_service.embed(description)

        # Find similar objectives using similarity service
        similarity_service = SimilarityService()
        similar = similarity_service.find_similar_objectives(
            embedding=embedding,
            limit=limit,
            exclude_id=exclude_objective_id if exclude_objective_id else None,
        )

        similar_objectives = [
            {
                "objective_id": s.objective_id,
                "title": s.title,
                "similarity": round(s.similarity, 3),
            }
            for s in similar
        ]

        return {
            "success": True,
            "similar_objectives": similar_objectives,
            "message": f"Found {len(similar)} similar objectives",
        }

    except Exception as e:
        logger.error(f"Error finding similar objectives: {e}", exc_info=True)
        return {
            "success": False,
            "similar_objectives": [],
            "message": f"Error finding similar objectives: {str(e)}",
        }


def get_sub_objectives(
    objective_id: str,
) -> dict:
    """Get child objectives that contribute to a parent objective.

    Args:
        objective_id: The ID of the parent objective.

    Returns:
        Dictionary with success status and list of sub-objectives.
    """
    try:
        if not objective_id or not objective_id.strip():
            return {
                "success": False,
                "sub_objectives": [],
                "message": "objective_id is required",
            }

        # Verify objective exists
        objective = ObjectiveActions.get_by_id(objective_id)
        if not objective:
            return {
                "success": False,
                "sub_objectives": [],
                "message": f"Objective {objective_id} not found",
            }

        # Get sub-objectives
        sub_objectives = ObjectiveActions.get_sub_objectives(objective_id)

        sub_list = [
            {
                "objective_id": o.id,
                "title": o.title,
                "description": o.description[:200] + "..." if len(o.description) > 200 else o.description,
                "status": o.status,
            }
            for o in sub_objectives
        ]

        return {
            "success": True,
            "sub_objectives": sub_list,
            "count": len(sub_list),
            "message": f"Found {len(sub_list)} sub-objectives",
        }

    except Exception as e:
        logger.error(f"Error getting sub-objectives: {e}", exc_info=True)
        return {
            "success": False,
            "sub_objectives": [],
            "count": 0,
            "message": f"Error getting sub-objectives: {str(e)}",
        }


def retire_objective(
    objective_id: str,
) -> dict:
    """Retire an objective (soft delete).

    This triggers review of linked ideas by the ObjectiveAgent.

    Args:
        objective_id: The ID of the objective to retire.

    Returns:
        Dictionary with success status and message.
    """
    try:
        if not objective_id or not objective_id.strip():
            return {
                "success": False,
                "message": "objective_id is required",
            }

        # Verify objective exists
        objective = ObjectiveActions.get_by_id(objective_id)
        if not objective:
            return {
                "success": False,
                "message": f"Objective {objective_id} not found",
            }

        if objective.status == "Retired":
            return {
                "success": False,
                "message": f"Objective {objective_id} is already retired",
            }

        # Retire the objective
        ObjectiveActions.retire(objective_id)
        logger.info(f"Retired objective: {objective_id}")

        return {
            "success": True,
            "objective_id": objective_id,
            "message": "Objective retired successfully. Linked ideas will be reviewed.",
        }

    except Exception as e:
        logger.error(f"Error retiring objective: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error retiring objective: {str(e)}",
        }
