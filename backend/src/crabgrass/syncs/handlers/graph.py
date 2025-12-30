"""Graph handlers - populate graph edges when relationships change.

These handlers maintain the graph edge tables that enable property graph
queries and hybrid vector+graph searches.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def update_objective_hierarchy(sender, objective_id: str, parent_id: str = None, **kwargs) -> None:
    """Update objective hierarchy graph when objective created/updated.

    Called when: objective.created, objective.updated (if parent_id changed)
    Maintains the graph_objective_hierarchy table for efficient traversal.
    """
    try:
        from crabgrass.database import execute, fetchall

        # Remove existing hierarchy edges for this objective as child
        execute(
            "DELETE FROM graph_objective_hierarchy WHERE child_id = ?",
            [objective_id],
        )

        if parent_id:
            # Add direct edge
            now = datetime.utcnow()
            execute(
                """
                INSERT INTO graph_objective_hierarchy (parent_id, child_id, depth, created_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT (parent_id, child_id) DO NOTHING
                """,
                [parent_id, objective_id, now],
            )

            # Also add transitive edges (grandparent -> this objective)
            # This materializes the full ancestry for efficient queries
            ancestors = fetchall(
                """
                SELECT parent_id, depth FROM graph_objective_hierarchy
                WHERE child_id = ?
                """,
                [parent_id],
            )

            for ancestor_id, ancestor_depth in ancestors:
                execute(
                    """
                    INSERT INTO graph_objective_hierarchy (parent_id, child_id, depth, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT (parent_id, child_id) DO NOTHING
                    """,
                    [ancestor_id, objective_id, ancestor_depth + 1, now],
                )

            logger.debug(f"Updated hierarchy for objective {objective_id} under {parent_id}")

    except Exception as e:
        logger.error(f"Error updating objective hierarchy for {objective_id}: {e}")


def record_idea_objective_link(sender, idea_id: str, objective_id: str, **kwargs) -> None:
    """Record when idea is linked to objective (for graph traversal).

    Called when: idea.linked_to_objective
    The idea_objectives table already exists, but this handler can do additional
    graph maintenance if needed.
    """
    logger.debug(f"Recorded idea-objective link: {idea_id} -> {objective_id}")


def remove_idea_objective_link(sender, idea_id: str, objective_id: str, **kwargs) -> None:
    """Handle when idea is unlinked from objective.

    Called when: idea.unlinked_from_objective
    """
    logger.debug(f"Removed idea-objective link: {idea_id} -> {objective_id}")


def record_similarity_edge(
    sender,
    source_type: str,
    source_id: str,
    source_idea_id: str,
    target_type: str,
    target_idea_id: str,
    similarity_score: float,
    **kwargs,
) -> None:
    """Record a similarity edge discovered by ConnectionAgent.

    Called when: agent.found_similarity
    Records to the relationships table (which batch job later processes into graph tables).
    """
    try:
        from crabgrass.database import execute
        from uuid import uuid4

        relationship_id = str(uuid4())
        now = datetime.utcnow()

        # Store in relationships table (source of truth)
        execute(
            """
            INSERT INTO relationships (id, from_type, from_id, to_type, to_id, relationship, score, discovered_at, discovered_by)
            VALUES (?, ?, ?, ?, ?, 'similar', ?, ?, 'ConnectionAgent')
            ON CONFLICT DO NOTHING
            """,
            [relationship_id, source_type, source_idea_id, target_type, target_idea_id, similarity_score, now],
        )

        logger.debug(
            f"Recorded similarity: {source_type}:{source_idea_id} -> {target_type}:{target_idea_id} "
            f"(score: {similarity_score:.3f})"
        )

    except Exception as e:
        logger.error(f"Error recording similarity edge: {e}")
