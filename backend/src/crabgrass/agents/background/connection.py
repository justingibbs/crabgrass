"""ConnectionAgent - discovers relationships between concepts.

This agent processes the CONNECTION queue and finds similar content
across Ideas, Challenges, Approaches, and Summaries. It emits signals
that trigger graph relationship creation and user notifications.

Uses embedding-based nearest neighbor search to find similarities.
"""

import logging

from crabgrass.agents.runner import BackgroundAgent
from crabgrass.concepts.queue import QueueName, QueueItem
from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.summary import SummaryActions
from crabgrass.concepts.challenge import ChallengeActions
from crabgrass.concepts.approach import ApproachActions
from crabgrass.services.similarity import SimilarityService
from crabgrass.syncs.signals import agent_found_similarity

logger = logging.getLogger(__name__)

# Similarity threshold - only report matches above this score
SIMILARITY_THRESHOLD = 0.7
# Maximum similar items to find
MAX_SIMILAR = 5


class ConnectionAgent(BackgroundAgent):
    """Analyzes concepts to discover relationships.

    Finds similar Challenges, Approaches, Summaries, and related Ideas.
    Emits signals that create graph relationships and queue notifications.
    """

    def __init__(self):
        super().__init__(QueueName.CONNECTION)
        self._similarity_service = None

    @property
    def similarity_service(self) -> SimilarityService:
        """Lazy-load similarity service."""
        if self._similarity_service is None:
            self._similarity_service = SimilarityService()
        return self._similarity_service

    async def process_item(self, item: QueueItem) -> None:
        """Process a connection queue item.

        Args:
            item: Queue item with payload containing idea_id, summary_id,
                  challenge_id, or approach_id
        """
        payload = item.payload
        logger.info(f"ConnectionAgent: Processing item {item.id}")
        logger.debug(f"ConnectionAgent: Payload = {payload}")

        try:
            if payload.get("challenge_id"):
                await self._find_similar_challenges(
                    payload["challenge_id"],
                    payload.get("idea_id"),
                )

            elif payload.get("approach_id"):
                await self._find_similar_approaches(
                    payload["approach_id"],
                    payload.get("idea_id"),
                )

            elif payload.get("summary_id"):
                await self._find_similar_summaries(
                    payload["summary_id"],
                    payload.get("idea_id"),
                )

            elif payload.get("idea_id"):
                # General idea connection - find related via summary
                await self._find_related_ideas(payload["idea_id"])

            logger.info(f"ConnectionAgent: Completed item {item.id}")

        except Exception as e:
            logger.error(f"ConnectionAgent: Error processing item {item.id}: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # Similarity Discovery Methods
    # ─────────────────────────────────────────────────────────────────────────

    async def _find_similar_challenges(self, challenge_id: str, idea_id: str | None) -> None:
        """Find challenges with similar content.

        Emits: agent.found_similarity for each match above threshold
        """
        challenge = ChallengeActions.get_by_id(challenge_id)
        if not challenge or not challenge.embedding:
            logger.debug(f"Challenge {challenge_id} has no embedding, skipping")
            return

        # Get the idea_id if not provided
        if not idea_id:
            idea_id = challenge.idea_id

        similar = self.similarity_service.find_similar_challenges(
            embedding=challenge.embedding,
            limit=MAX_SIMILAR,
            exclude_idea_id=idea_id,
        )

        for match in similar:
            if match.similarity >= SIMILARITY_THRESHOLD:
                logger.info(
                    f"ConnectionAgent: Found similar challenge - "
                    f"idea {idea_id} <-> {match.idea_id} (score: {match.similarity:.3f})"
                )
                agent_found_similarity.send(
                    None,
                    source_type="challenge",
                    source_id=challenge_id,
                    source_idea_id=idea_id,
                    target_type="challenge",
                    target_idea_id=match.idea_id,
                    similarity_score=match.similarity,
                )

    async def _find_similar_approaches(self, approach_id: str, idea_id: str | None) -> None:
        """Find approaches with similar content.

        Emits: agent.found_similarity for each match above threshold
        """
        approach = ApproachActions.get_by_id(approach_id)
        if not approach or not approach.embedding:
            logger.debug(f"Approach {approach_id} has no embedding, skipping")
            return

        if not idea_id:
            idea_id = approach.idea_id

        similar = self.similarity_service.find_similar_approaches(
            embedding=approach.embedding,
            limit=MAX_SIMILAR,
            exclude_idea_id=idea_id,
        )

        for match in similar:
            if match.similarity >= SIMILARITY_THRESHOLD:
                logger.info(
                    f"ConnectionAgent: Found similar approach - "
                    f"idea {idea_id} <-> {match.idea_id} (score: {match.similarity:.3f})"
                )
                agent_found_similarity.send(
                    None,
                    source_type="approach",
                    source_id=approach_id,
                    source_idea_id=idea_id,
                    target_type="approach",
                    target_idea_id=match.idea_id,
                    similarity_score=match.similarity,
                )

    async def _find_similar_summaries(self, summary_id: str, idea_id: str | None) -> None:
        """Find summaries with similar content.

        Emits: agent.found_similarity for each match above threshold
        """
        summary = SummaryActions.get_by_id(summary_id)
        if not summary or not summary.embedding:
            logger.debug(f"Summary {summary_id} has no embedding, skipping")
            return

        if not idea_id:
            idea_id = summary.idea_id

        similar = self.similarity_service.find_similar_summaries(
            embedding=summary.embedding,
            limit=MAX_SIMILAR,
            exclude_idea_id=idea_id,
        )

        for match in similar:
            if match.similarity >= SIMILARITY_THRESHOLD:
                logger.info(
                    f"ConnectionAgent: Found similar summary - "
                    f"idea {idea_id} <-> {match.idea_id} (score: {match.similarity:.3f})"
                )
                agent_found_similarity.send(
                    None,
                    source_type="summary",
                    source_id=summary_id,
                    source_idea_id=idea_id,
                    target_type="summary",
                    target_idea_id=match.idea_id,
                    similarity_score=match.similarity,
                )

    async def _find_related_ideas(self, idea_id: str) -> None:
        """Find ideas related via any kernel element (summary, challenge, approach).

        Uses summary as the primary comparison since all ideas have one.
        """
        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            logger.warning(f"Idea {idea_id} not found")
            return

        # Get the summary for this idea
        summary = SummaryActions.get_by_idea_id(idea_id)
        if summary and summary.embedding:
            similar = self.similarity_service.find_similar_summaries(
                embedding=summary.embedding,
                limit=MAX_SIMILAR,
                exclude_idea_id=idea_id,
            )

            for match in similar:
                if match.similarity >= SIMILARITY_THRESHOLD:
                    logger.info(
                        f"ConnectionAgent: Found related idea - "
                        f"{idea_id} <-> {match.idea_id} (score: {match.similarity:.3f})"
                    )
                    agent_found_similarity.send(
                        None,
                        source_type="idea",
                        source_id=idea_id,
                        source_idea_id=idea_id,
                        target_type="idea",
                        target_idea_id=match.idea_id,
                        similarity_score=match.similarity,
                    )
