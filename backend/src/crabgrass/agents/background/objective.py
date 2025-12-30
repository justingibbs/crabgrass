"""ObjectiveAgent - handles objective lifecycle events.

This agent processes the OBJECTIVE_REVIEW queue when objectives are retired.
It analyzes orphaned ideas (previously linked to the retired objective) and
suggests reconnections to other active objectives using embedding similarity.

Queues notifications for the SurfacingAgent to deliver.
"""

import logging

from crabgrass.agents.runner import BackgroundAgent
from crabgrass.concepts.queue import QueueName, QueueItem, QueueActions
from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.summary import SummaryActions
from crabgrass.concepts.objective import ObjectiveActions
from crabgrass.concepts.idea_objective import IdeaObjectiveActions
from crabgrass.syncs.signals import agent_suggest_reconnection, agent_flag_orphan

logger = logging.getLogger(__name__)

# Similarity threshold for reconnection suggestions
RECONNECTION_THRESHOLD = 0.5
# Maximum objectives to suggest
MAX_SUGGESTIONS = 3


class ObjectiveAgent(BackgroundAgent):
    """Reviews Ideas when Objectives change.

    When Objectives are retired, identifies orphaned Ideas and analyzes
    whether new or existing Objectives are relevant matches.
    """

    def __init__(self):
        super().__init__(QueueName.OBJECTIVE_REVIEW)

    async def process_item(self, item: QueueItem) -> None:
        """Process an objective review queue item.

        Args:
            item: Queue item with payload containing idea_id and retired_objective_id
        """
        payload = item.payload
        logger.info(f"ObjectiveAgent: Processing item {item.id}")
        logger.debug(f"ObjectiveAgent: Payload = {payload}")

        idea_id = payload.get("idea_id")
        retired_objective_id = payload.get("retired_objective_id")

        if not idea_id:
            logger.warning(f"ObjectiveAgent: No idea_id in payload, skipping")
            return

        try:
            # Get the idea
            idea = IdeaActions.get_by_id(idea_id)
            if not idea:
                logger.warning(f"ObjectiveAgent: Idea {idea_id} not found")
                return

            # Check if idea still has other objective links
            remaining_links = IdeaObjectiveActions.get_objective_ids_for_idea(idea_id)
            # Filter to only active objectives
            active_links = []
            for obj_id in remaining_links:
                obj = ObjectiveActions.get_by_id(obj_id)
                if obj and obj.status == "Active":
                    active_links.append(obj_id)

            if active_links:
                # Idea still has active objective links, no action needed
                logger.info(
                    f"ObjectiveAgent: Idea {idea_id} still has {len(active_links)} active objective links"
                )
                return

            # Idea is orphaned - find potential reconnections
            suggestions = await self._find_reconnection_suggestions(idea_id)

            if suggestions:
                # Queue reconnection suggestions
                await self._queue_reconnection_suggestions(
                    idea=idea,
                    retired_objective_id=retired_objective_id,
                    suggestions=suggestions,
                )
            else:
                # No good matches found - flag as orphan
                await self._queue_orphan_alert(
                    idea=idea,
                    retired_objective_id=retired_objective_id,
                )

            logger.info(f"ObjectiveAgent: Completed item {item.id}")

        except Exception as e:
            logger.error(f"ObjectiveAgent: Error processing item {item.id}: {e}")
            raise

    async def _find_reconnection_suggestions(self, idea_id: str) -> list[dict]:
        """Find active objectives that might be relevant to this idea.

        Uses embedding similarity between idea summary and objective descriptions.
        """
        # Get the idea's summary embedding
        summary = SummaryActions.get_by_idea_id(idea_id)
        if not summary or not summary.embedding:
            logger.debug(f"ObjectiveAgent: Idea {idea_id} has no summary embedding")
            return []

        # Get active objectives with embeddings
        objectives = ObjectiveActions.list_active()

        results = []
        for objective in objectives:
            if not objective.embedding:
                continue

            # Calculate similarity
            similarity = self._calculate_similarity(
                summary.embedding,
                objective.embedding,
            )

            if similarity >= RECONNECTION_THRESHOLD:
                results.append({
                    "objective_id": objective.id,
                    "title": objective.title,
                    "similarity": similarity,
                })

        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:MAX_SUGGESTIONS]

        if results:
            logger.info(
                f"ObjectiveAgent: Found {len(results)} reconnection suggestions for idea {idea_id}"
            )

        return results

    def _calculate_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        import math

        # Dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))

        # Magnitudes
        mag1 = math.sqrt(sum(a * a for a in embedding1))
        mag2 = math.sqrt(sum(b * b for b in embedding2))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    async def _queue_reconnection_suggestions(
        self,
        idea,
        retired_objective_id: str | None,
        suggestions: list[dict],
    ) -> None:
        """Queue reconnection suggestions for the SurfacingAgent."""
        # Emit signal for the top suggestion (triggers sync handlers)
        top = suggestions[0]
        agent_suggest_reconnection.send(
            None,
            idea_id=idea.id,
            suggested_objective_id=top["objective_id"],
            similarity_score=top["similarity"],
            retired_objective_id=retired_objective_id,
        )

        logger.info(
            f"ObjectiveAgent: Suggested reconnecting idea {idea.id} "
            f"to objective {top['objective_id']} (score: {top['similarity']:.3f})"
        )

    async def _queue_orphan_alert(
        self,
        idea,
        retired_objective_id: str | None,
    ) -> None:
        """Queue orphan alert when no reconnection suggestions found."""
        # Emit signal (triggers sync handlers to queue surfacing notification)
        agent_flag_orphan.send(
            None,
            idea_id=idea.id,
            retired_objective_id=retired_objective_id,
        )

        logger.info(f"ObjectiveAgent: Flagged idea {idea.id} as orphan")
