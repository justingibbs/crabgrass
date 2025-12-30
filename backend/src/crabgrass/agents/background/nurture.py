"""NurtureAgent - nurtures nascent ideas toward structure.

This agent processes the NURTURE queue and analyzes nascent ideas
(those with only a Summary) to help them evolve. It finds similar ideas
and suggests relevant objectives using embedding-based similarity.

Queues notifications for the SurfacingAgent to deliver.
"""

import logging

from crabgrass.agents.runner import BackgroundAgent
from crabgrass.concepts.queue import QueueName, QueueItem, QueueActions
from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.summary import SummaryActions
from crabgrass.concepts.challenge import ChallengeActions
from crabgrass.concepts.approach import ApproachActions
from crabgrass.concepts.objective import ObjectiveActions
from crabgrass.services.similarity import SimilarityService
from crabgrass.services.embedding import get_embedding_service

logger = logging.getLogger(__name__)

# Similarity thresholds
IDEA_SIMILARITY_THRESHOLD = 0.65
OBJECTIVE_SIMILARITY_THRESHOLD = 0.6
# Maximum items to find
MAX_SIMILAR_IDEAS = 3
MAX_SIMILAR_OBJECTIVES = 3


class NurtureAgent(BackgroundAgent):
    """Monitors nascent Ideas and provides gentle encouragement.

    Analyzes Summaries to find similar Ideas and suggest relevant Objectives.
    Queues nudges encouraging users to evolve their Ideas.
    """

    def __init__(self):
        super().__init__(QueueName.NURTURE)
        self._similarity_service = None
        self._embedding_service = None

    @property
    def similarity_service(self) -> SimilarityService:
        """Lazy-load similarity service."""
        if self._similarity_service is None:
            self._similarity_service = SimilarityService()
        return self._similarity_service

    @property
    def embedding_service(self):
        """Lazy-load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    async def process_item(self, item: QueueItem) -> None:
        """Process a nurture queue item.

        Args:
            item: Queue item with payload containing idea_id and/or summary_id
        """
        payload = item.payload
        logger.info(f"NurtureAgent: Processing item {item.id}")
        logger.debug(f"NurtureAgent: Payload = {payload}")

        idea_id = payload.get("idea_id")
        reason = payload.get("reason", "analysis")

        if not idea_id:
            logger.warning(f"NurtureAgent: No idea_id in payload, skipping")
            return

        try:
            # Check if idea still needs nurturing (no challenge or approach yet)
            if not self._needs_nurturing(idea_id):
                logger.info(f"NurtureAgent: Idea {idea_id} has structure, skipping nurture")
                return

            # Get the idea and its summary
            idea = IdeaActions.get_by_id(idea_id)
            if not idea:
                logger.warning(f"NurtureAgent: Idea {idea_id} not found")
                return

            summary = SummaryActions.get_by_idea_id(idea_id)
            if not summary:
                logger.warning(f"NurtureAgent: Idea {idea_id} has no summary")
                return

            # Find similar nascent ideas (for community connection)
            similar_ideas = await self._find_similar_nascent_ideas(idea_id, summary)

            # Find potentially relevant objectives
            relevant_objectives = await self._find_relevant_objectives(summary)

            # Queue nurture nudge notification if we found something useful
            if similar_ideas or relevant_objectives:
                await self._queue_nurture_notification(
                    idea=idea,
                    similar_ideas=similar_ideas,
                    relevant_objectives=relevant_objectives,
                )

            logger.info(f"NurtureAgent: Completed item {item.id}")

        except Exception as e:
            logger.error(f"NurtureAgent: Error processing item {item.id}: {e}")
            raise

    def _needs_nurturing(self, idea_id: str) -> bool:
        """Check if idea is still nascent (no challenge or approach).

        Returns True if idea should be nurtured.
        """
        challenge = ChallengeActions.get_by_idea_id(idea_id)
        approach = ApproachActions.get_by_idea_id(idea_id)

        # Idea needs nurturing if it lacks both challenge and approach
        return challenge is None and approach is None

    async def _find_similar_nascent_ideas(
        self,
        idea_id: str,
        summary,
    ) -> list[dict]:
        """Find other nascent ideas with similar summaries.

        Returns list of similar ideas for potential collaboration.
        """
        if not summary.embedding:
            logger.debug(f"Summary for idea {idea_id} has no embedding")
            return []

        similar = self.similarity_service.find_similar_summaries(
            embedding=summary.embedding,
            limit=MAX_SIMILAR_IDEAS + 5,  # Get extra to filter
            exclude_idea_id=idea_id,
        )

        # Filter to only nascent ideas above threshold
        results = []
        for match in similar:
            if match.similarity < IDEA_SIMILARITY_THRESHOLD:
                continue

            # Check if the matched idea is also nascent
            if self._needs_nurturing(match.idea_id):
                results.append({
                    "idea_id": match.idea_id,
                    "title": match.title,
                    "similarity": match.similarity,
                })

                if len(results) >= MAX_SIMILAR_IDEAS:
                    break

        if results:
            logger.info(
                f"NurtureAgent: Found {len(results)} similar nascent ideas for {idea_id}"
            )

        return results

    async def _find_relevant_objectives(self, summary) -> list[dict]:
        """Find objectives that might be relevant to this idea.

        Uses embedding similarity between summary and objective descriptions.
        """
        if not summary.embedding:
            return []

        # Get active objectives with embeddings
        objectives = ObjectiveActions.list_active()

        results = []
        for objective in objectives:
            if not objective.embedding:
                continue

            # Calculate similarity
            try:
                # Use cosine similarity via the embedding service
                similarity = self._calculate_similarity(
                    summary.embedding,
                    objective.embedding,
                )

                if similarity >= OBJECTIVE_SIMILARITY_THRESHOLD:
                    results.append({
                        "objective_id": objective.id,
                        "title": objective.title,
                        "similarity": similarity,
                    })
            except Exception as e:
                logger.debug(f"Error calculating similarity for objective {objective.id}: {e}")
                continue

        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:MAX_SIMILAR_OBJECTIVES]

        if results:
            logger.info(
                f"NurtureAgent: Found {len(results)} relevant objectives for idea"
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

    async def _queue_nurture_notification(
        self,
        idea,
        similar_ideas: list[dict],
        relevant_objectives: list[dict],
    ) -> None:
        """Queue a nurture nudge for the SurfacingAgent to deliver."""
        # Build message based on what we found
        parts = []

        if similar_ideas:
            count = len(similar_ideas)
            parts.append(f"Found {count} similar idea{'s' if count > 1 else ''} you might want to collaborate on")

        if relevant_objectives:
            count = len(relevant_objectives)
            top_obj = relevant_objectives[0]["title"]
            parts.append(f"Your idea might align with objective: {top_obj}")

        if not parts:
            return

        message = ". ".join(parts)

        # Queue for surfacing
        QueueActions.enqueue(
            queue=QueueName.SURFACING,
            payload={
                "type": "nurture_nudge",
                "idea_id": idea.id,
                "idea_title": idea.title,
                "author_id": idea.author_id,
                "message": message,
                "similar_ideas": similar_ideas,
                "relevant_objectives": relevant_objectives,
            },
        )

        logger.info(f"NurtureAgent: Queued nurture notification for idea {idea.id}")
