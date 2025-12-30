"""ObjectiveAgent - handles objective lifecycle events.

This agent processes the OBJECTIVE_REVIEW queue when objectives are retired.
It analyzes orphaned ideas and suggests reconnections to other objectives.

Phase 1: Stub implementation that logs processing.
Phase 2+: Full LLM analysis and reconnection suggestions.
"""

import logging

from crabgrass.agents.runner import BackgroundAgent
from crabgrass.concepts.queue import QueueName, QueueItem

logger = logging.getLogger(__name__)


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

        # Phase 1: Log what we would do
        logger.info(f"ObjectiveAgent: Would review idea {idea_id} after objective {retired_objective_id} retired")

        # TODO Phase 2: Get idea with details
        # idea = await self._get_idea_with_details(idea_id)

        # TODO Phase 2: Get all active objectives
        # active_objectives = await self._list_active_objectives()

        # TODO Phase 2: Find best matching objective
        # best_match = await self._find_best_objective_match(idea, active_objectives)

        # TODO Phase 2: Emit appropriate signal
        # if best_match and best_match["score"] > 0.7:
        #     agent_suggest_reconnection.send(...)
        # else:
        #     agent_flag_orphan.send(...)

        logger.info(f"ObjectiveAgent: Completed item {item.id}")

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2+ Implementation Methods (stubs)
    # ─────────────────────────────────────────────────────────────────────────

    async def _get_idea_with_details(self, idea_id: str):
        """Load idea with all details.

        TODO Phase 2: Implement
        """
        pass

    async def _list_active_objectives(self) -> list:
        """Get all active objectives.

        TODO Phase 2: Implement
        """
        return []

    async def _find_best_objective_match(self, idea, objectives: list) -> dict | None:
        """Use LLM to find best matching objective.

        TODO Phase 2: Implement using LLMService
        """
        return None
