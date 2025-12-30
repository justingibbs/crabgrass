"""SurfacingAgent - creates notifications for users.

This agent processes the SURFACING queue and creates notifications
for relevant users based on various events (similar found, idea linked,
nurture nudges, etc.).

Phase 1: Stub implementation that logs processing.
Phase 2+: Full notification creation with user targeting.
"""

import logging

from crabgrass.agents.runner import BackgroundAgent
from crabgrass.concepts.queue import QueueName, QueueItem

logger = logging.getLogger(__name__)


class SurfacingAgent(BackgroundAgent):
    """Reviews queue items and creates Notifications for relevant Users.

    Determines who should be alerted and creates appropriate notifications
    based on the event type.
    """

    def __init__(self):
        super().__init__(QueueName.SURFACING)

    async def process_item(self, item: QueueItem) -> None:
        """Process a surfacing queue item.

        Args:
            item: Queue item with payload containing type and event details
        """
        payload = item.payload
        logger.info(f"SurfacingAgent: Processing item {item.id}")
        logger.debug(f"SurfacingAgent: Payload = {payload}")

        event_type = payload.get("type")
        if not event_type:
            logger.warning(f"SurfacingAgent: No type in payload, skipping")
            return

        # Phase 1: Log what we would do based on event type
        handler_name = f"_handle_{event_type}"
        logger.info(f"SurfacingAgent: Would handle event type '{event_type}'")

        # TODO Phase 2: Dispatch to type-specific handler
        # handler = getattr(self, handler_name, None)
        # if handler:
        #     await handler(payload)
        # else:
        #     logger.warning(f"SurfacingAgent: Unknown event type '{event_type}'")

        logger.info(f"SurfacingAgent: Completed item {item.id}")

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2+ Event Handlers (stubs)
    # ─────────────────────────────────────────────────────────────────────────

    async def _handle_idea_linked(self, payload: dict) -> None:
        """Notify objective watchers when idea linked.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_similar_found(self, payload: dict) -> None:
        """Notify users when similar content found.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_nurture_nudge(self, payload: dict) -> None:
        """Create nurture notification for idea author.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_objective_created(self, payload: dict) -> None:
        """Notify parent objective watchers of new sub-objective.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_objective_updated(self, payload: dict) -> None:
        """Notify watchers when objective is updated.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_objective_retired(self, payload: dict) -> None:
        """Notify watchers when objective retired.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_orphan_alert(self, payload: dict) -> None:
        """Alert contributors when idea loses objective link.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_reconnection_suggestion(self, payload: dict) -> None:
        """Suggest reconnecting orphaned idea to new objective.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_user_interest(self, payload: dict) -> None:
        """Notify user when they may be interested in an idea.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_shared_content_updated(self, payload: dict) -> None:
        """Notify ideas sharing content that was updated.

        TODO Phase 2: Implement
        """
        pass

    async def _handle_idea_archived(self, payload: dict) -> None:
        """Notify contributors when idea is archived.

        TODO Phase 2: Implement
        """
        pass
