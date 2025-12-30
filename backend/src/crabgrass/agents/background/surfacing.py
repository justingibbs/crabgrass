"""SurfacingAgent - creates notifications for users.

This agent processes the SURFACING queue and creates notifications
for relevant users based on various events (similar found, idea linked,
nurture nudges, etc.).

Uses template-based messages for notifications.
"""

import logging

from crabgrass.agents.runner import BackgroundAgent
from crabgrass.concepts.queue import QueueName, QueueItem
from crabgrass.concepts.notification import NotificationActions, NotificationType
from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.objective import ObjectiveActions
from crabgrass.concepts.watch import WatchActions

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

        try:
            # Dispatch to type-specific handler
            handler_name = f"_handle_{event_type}"
            handler = getattr(self, handler_name, None)

            if handler:
                await handler(payload)
            else:
                logger.warning(f"SurfacingAgent: Unknown event type '{event_type}'")

            logger.info(f"SurfacingAgent: Completed item {item.id}")

        except Exception as e:
            logger.error(f"SurfacingAgent: Error processing item {item.id}: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # Event Handlers
    # ─────────────────────────────────────────────────────────────────────────

    async def _handle_idea_linked(self, payload: dict) -> None:
        """Notify objective watchers when idea linked.

        Template: "A new idea '{title}' has been linked to {objective_title}"
        """
        idea_id = payload.get("idea_id")
        objective_id = payload.get("objective_id")

        if not idea_id or not objective_id:
            return

        idea = IdeaActions.get_by_id(idea_id)
        objective = ObjectiveActions.get_by_id(objective_id)

        if not idea or not objective:
            return

        # Get watchers of this objective
        watchers = WatchActions.get_objective_watchers(objective_id)

        # Don't notify the person who linked it (if they're watching)
        author_id = idea.author_id
        watchers = [w for w in watchers if w != author_id]

        for user_id in watchers:
            NotificationActions.create(
                user_id=user_id,
                type=NotificationType.IDEA_LINKED,
                message=f"A new idea '{idea.title}' has been linked to '{objective.title}'",
                source_type="objective",
                source_id=objective_id,
                related_id=idea_id,
            )

        if watchers:
            logger.info(f"SurfacingAgent: Notified {len(watchers)} watchers of idea link")

    async def _handle_similar_found(self, payload: dict) -> None:
        """Notify users when similar content found.

        Template: "Found similar {type}: '{title}' (similarity: {score}%)"
        """
        source_idea_id = payload.get("source_idea_id")
        target_idea_id = payload.get("target_idea_id")
        similarity_score = payload.get("similarity_score", 0)
        source_type = payload.get("source_type", "idea")

        if not source_idea_id or not target_idea_id:
            return

        source_idea = IdeaActions.get_by_id(source_idea_id)
        target_idea = IdeaActions.get_by_id(target_idea_id)

        if not source_idea or not target_idea:
            return

        # Notify the author of the source idea
        score_pct = int(similarity_score * 100)
        NotificationActions.create(
            user_id=source_idea.author_id,
            type=NotificationType.SIMILAR_FOUND,
            message=f"Found similar idea: '{target_idea.title}' ({score_pct}% match)",
            source_type="idea",
            source_id=source_idea_id,
            related_id=target_idea_id,
        )

        logger.info(f"SurfacingAgent: Notified {source_idea.author_id} of similar idea")

    async def _handle_nurture_nudge(self, payload: dict) -> None:
        """Create nurture notification for idea author.

        Message is pre-built by NurtureAgent.
        """
        idea_id = payload.get("idea_id")
        author_id = payload.get("author_id")
        message = payload.get("message")

        if not idea_id or not author_id or not message:
            return

        NotificationActions.create(
            user_id=author_id,
            type=NotificationType.NURTURE_NUDGE,
            message=message,
            source_type="idea",
            source_id=idea_id,
        )

        logger.info(f"SurfacingAgent: Created nurture nudge for idea {idea_id}")

    async def _handle_objective_created(self, payload: dict) -> None:
        """Notify parent objective watchers of new sub-objective.

        Template: "New sub-objective '{title}' created under '{parent_title}'"
        """
        objective_id = payload.get("objective_id")
        parent_id = payload.get("parent_id")

        if not objective_id or not parent_id:
            return

        objective = ObjectiveActions.get_by_id(objective_id)
        parent = ObjectiveActions.get_by_id(parent_id)

        if not objective or not parent:
            return

        # Get watchers of parent objective
        watchers = WatchActions.get_objective_watchers(parent_id)

        # Don't notify the creator
        watchers = [w for w in watchers if w != objective.author_id]

        for user_id in watchers:
            NotificationActions.create(
                user_id=user_id,
                type=NotificationType.CONTRIBUTION,
                message=f"New sub-objective '{objective.title}' created under '{parent.title}'",
                source_type="objective",
                source_id=parent_id,
                related_id=objective_id,
            )

        if watchers:
            logger.info(f"SurfacingAgent: Notified {len(watchers)} watchers of new sub-objective")

    async def _handle_objective_updated(self, payload: dict) -> None:
        """Notify watchers when objective is updated.

        Template: "Objective '{title}' has been updated"
        """
        objective_id = payload.get("objective_id")

        if not objective_id:
            return

        objective = ObjectiveActions.get_by_id(objective_id)
        if not objective:
            return

        # Get watchers
        watchers = WatchActions.get_objective_watchers(objective_id)

        # Don't notify the updater (assume it's the author for now)
        watchers = [w for w in watchers if w != objective.author_id]

        for user_id in watchers:
            NotificationActions.create(
                user_id=user_id,
                type=NotificationType.CONTRIBUTION,
                message=f"Objective '{objective.title}' has been updated",
                source_type="objective",
                source_id=objective_id,
            )

        if watchers:
            logger.info(f"SurfacingAgent: Notified {len(watchers)} watchers of objective update")

    async def _handle_objective_retired(self, payload: dict) -> None:
        """Notify watchers when objective retired.

        Template: "Objective '{title}' has been retired"
        """
        objective_id = payload.get("objective_id")

        if not objective_id:
            return

        objective = ObjectiveActions.get_by_id(objective_id)
        if not objective:
            return

        # Get watchers
        watchers = WatchActions.get_objective_watchers(objective_id)

        for user_id in watchers:
            NotificationActions.create(
                user_id=user_id,
                type=NotificationType.OBJECTIVE_RETIRED,
                message=f"Objective '{objective.title}' has been retired",
                source_type="objective",
                source_id=objective_id,
            )

        if watchers:
            logger.info(f"SurfacingAgent: Notified {len(watchers)} watchers of objective retirement")

    async def _handle_orphan_alert(self, payload: dict) -> None:
        """Alert contributors when idea loses objective link.

        Template: "Your idea '{title}' is no longer linked to an active objective"
        """
        idea_id = payload.get("idea_id")
        retired_objective_id = payload.get("retired_objective_id")

        if not idea_id:
            return

        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            return

        NotificationActions.create(
            user_id=idea.author_id,
            type=NotificationType.ORPHAN_ALERT,
            message=f"Your idea '{idea.title}' is no longer linked to an active objective",
            source_type="idea",
            source_id=idea_id,
            related_id=retired_objective_id,
        )

        logger.info(f"SurfacingAgent: Created orphan alert for idea {idea_id}")

    async def _handle_reconnection_suggestion(self, payload: dict) -> None:
        """Suggest reconnecting orphaned idea to new objective.

        Template: "Your idea '{idea_title}' might align with '{objective_title}'"
        """
        idea_id = payload.get("idea_id")
        suggested_objective_id = payload.get("suggested_objective_id")
        similarity_score = payload.get("similarity_score", 0)

        if not idea_id or not suggested_objective_id:
            return

        idea = IdeaActions.get_by_id(idea_id)
        objective = ObjectiveActions.get_by_id(suggested_objective_id)

        if not idea or not objective:
            return

        score_pct = int(similarity_score * 100)
        NotificationActions.create(
            user_id=idea.author_id,
            type=NotificationType.RECONNECTION_SUGGESTION,
            message=f"Your idea '{idea.title}' might align with '{objective.title}' ({score_pct}% match)",
            source_type="idea",
            source_id=idea_id,
            related_id=suggested_objective_id,
        )

        logger.info(f"SurfacingAgent: Created reconnection suggestion for idea {idea_id}")

    async def _handle_user_interest(self, payload: dict) -> None:
        """Notify user when they may be interested in an idea.

        Template: "You might be interested in: '{title}'"
        """
        user_id = payload.get("user_id")
        idea_id = payload.get("idea_id")

        if not user_id or not idea_id:
            return

        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            return

        # Don't notify the author of their own idea
        if idea.author_id == user_id:
            return

        NotificationActions.create(
            user_id=user_id,
            type=NotificationType.SIMILAR_FOUND,
            message=f"You might be interested in: '{idea.title}'",
            source_type="idea",
            source_id=idea_id,
        )

        logger.info(f"SurfacingAgent: Notified {user_id} of interesting idea")

    async def _handle_shared_content_updated(self, payload: dict) -> None:
        """Notify ideas sharing content that was updated.

        Template: "Content shared with your idea has been updated"
        """
        source_idea_id = payload.get("source_idea_id")
        related_idea_ids = payload.get("related_idea_ids", [])

        if not source_idea_id or not related_idea_ids:
            return

        source_idea = IdeaActions.get_by_id(source_idea_id)
        if not source_idea:
            return

        for related_id in related_idea_ids:
            related_idea = IdeaActions.get_by_id(related_id)
            if related_idea and related_idea.author_id != source_idea.author_id:
                NotificationActions.create(
                    user_id=related_idea.author_id,
                    type=NotificationType.CONTRIBUTION,
                    message=f"Content related to your idea '{related_idea.title}' has been updated",
                    source_type="idea",
                    source_id=related_id,
                    related_id=source_idea_id,
                )

        if related_idea_ids:
            logger.info(f"SurfacingAgent: Notified users of shared content update")

    async def _handle_idea_archived(self, payload: dict) -> None:
        """Notify contributors when idea is archived.

        Template: "Idea '{title}' has been archived"
        """
        idea_id = payload.get("idea_id")

        if not idea_id:
            return

        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            return

        # Get idea watchers (if any)
        watchers = WatchActions.get_idea_watchers(idea_id)

        # Don't notify the author (they did it)
        watchers = [w for w in watchers if w != idea.author_id]

        for user_id in watchers:
            NotificationActions.create(
                user_id=user_id,
                type=NotificationType.CONTRIBUTION,
                message=f"Idea '{idea.title}' has been archived",
                source_type="idea",
                source_id=idea_id,
            )

        if watchers:
            logger.info(f"SurfacingAgent: Notified {len(watchers)} watchers of idea archive")
