"""Enqueue handlers - add items to async processing queues.

These handlers are called by sync signals and add items to queues
for background agents to process. This decouples the sync response
from the actual processing work.

Handlers are plain functions with NO decorators. They're wired
to signals via the registry at startup.
"""

import logging

from crabgrass.concepts.queue import QueueActions, QueueName

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Connection Queue Handlers
# ─────────────────────────────────────────────────────────────────────────────


def enqueue_connection(sender, **kwargs) -> None:
    """Add item to ConnectionQueue for relationship discovery.

    ConnectionAgent will find similar content and create relationships.

    Called when: summary.updated, challenge.created, challenge.updated,
                 approach.created, approach.updated, idea.created, idea.updated
    """
    try:
        payload = {
            "idea_id": kwargs.get("idea_id"),
            "summary_id": kwargs.get("summary_id"),
            "challenge_id": kwargs.get("challenge_id"),
            "approach_id": kwargs.get("approach_id"),
            "content": kwargs.get("content"),
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        QueueActions.enqueue(QueueName.CONNECTION, payload)
        logger.info(f"Enqueued connection item: {payload}")
    except Exception as e:
        logger.error(f"Error enqueueing connection item: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Nurture Queue Handlers
# ─────────────────────────────────────────────────────────────────────────────


def enqueue_nurture(sender, **kwargs) -> None:
    """Add Summary to NurtureQueue for analysis.

    NurtureAgent will analyze for implicit challenges and find similar ideas.

    Called when: summary.created, summary.updated
    """
    try:
        payload = {
            "summary_id": kwargs.get("summary_id"),
            "idea_id": kwargs.get("idea_id"),
            "content": kwargs.get("content"),
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        QueueActions.enqueue(QueueName.NURTURE, payload)
        logger.info(f"Enqueued nurture item: {payload}")
    except Exception as e:
        logger.error(f"Error enqueueing nurture item: {e}")


def enqueue_nurture_if_summary_only(sender, idea_id: str, **kwargs) -> None:
    """Add to NurtureQueue only if idea has no structure yet.

    Called when: idea.created
    """
    try:
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.challenge import ChallengeActions
        from crabgrass.concepts.approach import ApproachActions

        # Check if idea has structure
        challenge = ChallengeActions.get_by_idea_id(idea_id)
        approach = ApproachActions.get_by_idea_id(idea_id)

        if challenge is None and approach is None:
            payload = {
                "idea_id": idea_id,
                "reason": "summary_only",
            }
            QueueActions.enqueue(QueueName.NURTURE, payload)
            logger.info(f"Enqueued nascent idea {idea_id} for nurturing")
        else:
            logger.debug(f"Idea {idea_id} has structure, skipping nurture queue")
    except Exception as e:
        logger.error(f"Error checking/enqueueing nurture for idea {idea_id}: {e}")


def remove_from_nurture_queue(sender, idea_id: str, **kwargs) -> None:
    """Remove idea from NurtureQueue (it's evolving, gained structure).

    Called when: idea.linked_to_objective, idea.structure_added
    """
    try:
        removed = QueueActions.remove_by_payload_match(QueueName.NURTURE, idea_id=idea_id)
        if removed > 0:
            logger.info(f"Removed {removed} nurture items for idea {idea_id}")
    except Exception as e:
        logger.error(f"Error removing nurture items for idea {idea_id}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Surfacing Queue Handlers
# ─────────────────────────────────────────────────────────────────────────────


def enqueue_surfacing_linked(sender, idea_id: str, objective_id: str, **kwargs) -> None:
    """Queue notification for objective watchers when idea linked.

    Called when: idea.linked_to_objective
    """
    try:
        payload = {
            "type": "idea_linked",
            "idea_id": idea_id,
            "objective_id": objective_id,
        }
        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for idea {idea_id} linked to objective {objective_id}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for linked idea: {e}")


def enqueue_surfacing_archived(sender, idea_id: str, **kwargs) -> None:
    """Notify contributors when idea is archived.

    Called when: idea.archived
    """
    try:
        payload = {
            "type": "idea_archived",
            "idea_id": idea_id,
        }
        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for archived idea {idea_id}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for archived idea: {e}")


def enqueue_surfacing_shared_update(sender, **kwargs) -> None:
    """Notify Ideas sharing a Challenge/Approach when it's updated.

    Called when: challenge.updated, approach.updated
    """
    try:
        payload = {
            "type": "shared_content_updated",
            "challenge_id": kwargs.get("challenge_id"),
            "approach_id": kwargs.get("approach_id"),
            "content": kwargs.get("content"),
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for shared content update: {payload}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for shared update: {e}")


def enqueue_surfacing_objective_created(sender, objective_id: str, parent_id: str | None = None, **kwargs) -> None:
    """Notify parent objective watchers of new sub-objective.

    Called when: objective.created
    """
    try:
        if parent_id:
            payload = {
                "type": "objective_created",
                "objective_id": objective_id,
                "parent_id": parent_id,
            }
            QueueActions.enqueue(QueueName.SURFACING, payload)
            logger.info(f"Enqueued surfacing for new objective {objective_id} under parent {parent_id}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for objective created: {e}")


def enqueue_surfacing_objective_updated(sender, objective_id: str, **kwargs) -> None:
    """Notify watchers when objective is updated.

    Called when: objective.updated
    """
    try:
        payload = {
            "type": "objective_updated",
            "objective_id": objective_id,
            "changes": kwargs.get("changes", {}),
        }
        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for updated objective {objective_id}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for objective updated: {e}")


def enqueue_surfacing_objective_retired(sender, objective_id: str, **kwargs) -> None:
    """Notify watchers when objective is retired.

    Called when: objective.retired
    """
    try:
        payload = {
            "type": "objective_retired",
            "objective_id": objective_id,
        }
        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for retired objective {objective_id}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for objective retired: {e}")


def enqueue_surfacing_similarity(sender, **kwargs) -> None:
    """Notify users when similar content is found.

    Called when: agent.found_similarity
    """
    try:
        payload = {
            "type": "similar_found",
            "from_type": kwargs.get("from_type"),
            "from_id": kwargs.get("from_id"),
            "to_type": kwargs.get("to_type"),
            "to_id": kwargs.get("to_id"),
            "score": kwargs.get("score"),
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for similarity: {payload}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for similarity: {e}")


def enqueue_surfacing_interest(sender, user_id: str, idea_id: str, **kwargs) -> None:
    """Notify user when they may be interested in an idea.

    Called when: agent.found_relevant_user
    """
    try:
        payload = {
            "type": "user_interest",
            "user_id": user_id,
            "idea_id": idea_id,
            "score": kwargs.get("score"),
        }
        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for user {user_id} interest in idea {idea_id}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for user interest: {e}")


def enqueue_surfacing_reconnection(sender, idea_id: str, objective_id: str, **kwargs) -> None:
    """Suggest reconnecting orphaned idea to new objective.

    Called when: agent.suggest_reconnection
    """
    try:
        payload = {
            "type": "reconnection_suggestion",
            "idea_id": idea_id,
            "objective_id": objective_id,
            "score": kwargs.get("score"),
            "reason": kwargs.get("reason"),
        }
        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for reconnection: idea {idea_id} -> objective {objective_id}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for reconnection: {e}")


def enqueue_surfacing_orphan(sender, idea_id: str, **kwargs) -> None:
    """Alert contributors when idea loses objective link.

    Called when: agent.flag_orphan
    """
    try:
        payload = {
            "type": "orphan_alert",
            "idea_id": idea_id,
        }
        QueueActions.enqueue(QueueName.SURFACING, payload)
        logger.info(f"Enqueued surfacing for orphaned idea {idea_id}")
    except Exception as e:
        logger.error(f"Error enqueueing surfacing for orphan: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Objective Review Queue Handlers
# ─────────────────────────────────────────────────────────────────────────────


def enqueue_objective_review(sender, objective_id: str, **kwargs) -> None:
    """Add linked ideas to ObjectiveReviewQueue when objective retires.

    ObjectiveAgent will analyze ideas and suggest reconnections.

    Called when: objective.retired
    """
    try:
        from crabgrass.database import fetchall

        # Get all ideas linked to this objective
        rows = fetchall(
            """
            SELECT idea_id FROM idea_objectives WHERE objective_id = ?
            """,
            [objective_id],
        )

        for row in rows:
            idea_id = row[0]
            payload = {
                "idea_id": idea_id,
                "retired_objective_id": objective_id,
            }
            QueueActions.enqueue(QueueName.OBJECTIVE_REVIEW, payload)
            logger.info(f"Enqueued objective review for idea {idea_id}")

        logger.info(f"Enqueued {len(rows)} ideas for review after objective {objective_id} retired")
    except Exception as e:
        logger.error(f"Error enqueueing objective review: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Graph Relationship Handlers
# ─────────────────────────────────────────────────────────────────────────────


def create_similarity_relationship(sender, **kwargs) -> None:
    """Create IS_SIMILAR_TO or IS_RELATED_TO relationship in graph.

    Called when: agent.found_similarity
    """
    try:
        from crabgrass.database import execute
        from uuid import uuid4
        from datetime import datetime

        relationship_id = str(uuid4())
        now = datetime.utcnow()

        from_type = kwargs.get("from_type")
        from_id = kwargs.get("from_id")
        to_type = kwargs.get("to_type")
        to_id = kwargs.get("to_id")
        score = kwargs.get("score")

        # Determine relationship type
        if from_type == to_type:
            relationship = "IS_SIMILAR_TO"
        else:
            relationship = "IS_RELATED_TO"

        # Insert or update relationship
        execute(
            """
            INSERT INTO relationships (id, from_type, from_id, to_type, to_id, relationship, score, discovered_at, discovered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING
            """,
            [relationship_id, from_type, from_id, to_type, to_id, relationship, score, now, "connection_agent"],
        )

        logger.info(f"Created {relationship} relationship: {from_type}/{from_id} -> {to_type}/{to_id}")
    except Exception as e:
        logger.error(f"Error creating similarity relationship: {e}")


def create_interest_relationship(sender, user_id: str, idea_id: str, **kwargs) -> None:
    """Create MAY_BE_INTERESTED_IN relationship.

    Called when: agent.found_relevant_user
    """
    try:
        from crabgrass.database import execute
        from uuid import uuid4
        from datetime import datetime

        relationship_id = str(uuid4())
        now = datetime.utcnow()
        score = kwargs.get("score")

        execute(
            """
            INSERT INTO relationships (id, from_type, from_id, to_type, to_id, relationship, score, discovered_at, discovered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING
            """,
            [relationship_id, "user", user_id, "idea", idea_id, "MAY_BE_INTERESTED_IN", score, now, "connection_agent"],
        )

        logger.info(f"Created MAY_BE_INTERESTED_IN relationship: user/{user_id} -> idea/{idea_id}")
    except Exception as e:
        logger.error(f"Error creating interest relationship: {e}")
