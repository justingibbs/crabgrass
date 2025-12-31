"""Tests for background agents.

These tests verify agent behavior in isolation:
1. Queue consumption - dequeue, process, complete/fail
2. Signal emission - agent signals for similarity/orphan events
3. Notification creation - SurfacingAgent creating notifications

Agents tested:
- ConnectionAgent: Discovers relationships via embedding similarity
- NurtureAgent: Nurtures nascent ideas, finds similar content
- ObjectiveAgent: Handles orphan detection when objectives retire
- SurfacingAgent: Creates notifications from queue events
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────────────
# Test Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_queue_item():
    """Create a mock queue item for testing."""
    @dataclass
    class MockQueueItem:
        id: str
        payload: dict

    def _create(item_id: str = "queue-item-1", payload: dict = None):
        return MockQueueItem(id=item_id, payload=payload or {})
    return _create


@pytest.fixture
def mock_similarity_match():
    """Create mock similarity match results."""
    @dataclass
    class SimilarityMatch:
        idea_id: str
        title: str
        similarity: float

    def _create(idea_id: str = "idea-123", title: str = "Similar Idea", similarity: float = 0.85):
        return SimilarityMatch(idea_id=idea_id, title=title, similarity=similarity)
    return _create


@pytest.fixture
def signal_catcher():
    """Capture signals emitted during tests."""
    caught = []

    def handler(sender, **kwargs):
        caught.append({"sender": sender, **kwargs})

    return caught, handler


# ─────────────────────────────────────────────────────────────────────────────
# ConnectionAgent Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestConnectionAgent:
    """Tests for ConnectionAgent - discovers relationships via similarity."""

    @pytest.mark.asyncio
    async def test_processes_challenge_similarity(self, mock_queue_item, mock_similarity_match, signal_catcher):
        """ConnectionAgent should find similar challenges and emit signal."""
        caught, handler = signal_catcher

        # Mock the challenge with embedding
        mock_challenge = MagicMock()
        mock_challenge.embedding = [0.1] * 768
        mock_challenge.idea_id = "source-idea"

        # Mock similarity service to return matches
        similar_match = mock_similarity_match(idea_id="target-idea", similarity=0.85)

        with patch("crabgrass.agents.background.connection.ChallengeActions") as mock_challenge_actions, \
             patch("crabgrass.agents.background.connection.SimilarityService") as MockSimilarityService, \
             patch("crabgrass.agents.background.connection.agent_found_similarity") as mock_signal:

            mock_challenge_actions.get_by_id.return_value = mock_challenge

            mock_service = MagicMock()
            mock_service.find_similar_challenges.return_value = [similar_match]
            MockSimilarityService.return_value = mock_service

            # Connect signal handler
            mock_signal.send = MagicMock()

            from crabgrass.agents.background.connection import ConnectionAgent

            agent = ConnectionAgent()
            item = mock_queue_item(payload={"challenge_id": "chal-1", "idea_id": "source-idea"})
            await agent.process_item(item)

            # Verify similarity was searched
            mock_service.find_similar_challenges.assert_called_once()

            # Verify signal was emitted
            mock_signal.send.assert_called_once()
            call_kwargs = mock_signal.send.call_args[1]
            assert call_kwargs["source_type"] == "challenge"
            assert call_kwargs["source_idea_id"] == "source-idea"
            assert call_kwargs["target_idea_id"] == "target-idea"
            assert call_kwargs["similarity_score"] == 0.85

    @pytest.mark.asyncio
    async def test_skips_low_similarity_matches(self, mock_queue_item, mock_similarity_match):
        """ConnectionAgent should not emit signals for matches below threshold."""
        mock_challenge = MagicMock()
        mock_challenge.embedding = [0.1] * 768
        mock_challenge.idea_id = "source-idea"

        # Low similarity match (below 0.7 threshold)
        low_match = mock_similarity_match(idea_id="low-match", similarity=0.5)

        with patch("crabgrass.agents.background.connection.ChallengeActions") as mock_challenge_actions, \
             patch("crabgrass.agents.background.connection.SimilarityService") as MockSimilarityService, \
             patch("crabgrass.agents.background.connection.agent_found_similarity") as mock_signal:

            mock_challenge_actions.get_by_id.return_value = mock_challenge

            mock_service = MagicMock()
            mock_service.find_similar_challenges.return_value = [low_match]
            MockSimilarityService.return_value = mock_service

            from crabgrass.agents.background.connection import ConnectionAgent

            agent = ConnectionAgent()
            item = mock_queue_item(payload={"challenge_id": "chal-1"})
            await agent.process_item(item)

            # Signal should NOT be emitted for low similarity
            mock_signal.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_processes_approach_similarity(self, mock_queue_item, mock_similarity_match):
        """ConnectionAgent should find similar approaches and emit signal."""
        mock_approach = MagicMock()
        mock_approach.embedding = [0.2] * 768
        mock_approach.idea_id = "source-idea"

        similar_match = mock_similarity_match(idea_id="target-idea", similarity=0.8)

        with patch("crabgrass.agents.background.connection.ApproachActions") as mock_approach_actions, \
             patch("crabgrass.agents.background.connection.SimilarityService") as MockSimilarityService, \
             patch("crabgrass.agents.background.connection.agent_found_similarity") as mock_signal:

            mock_approach_actions.get_by_id.return_value = mock_approach

            mock_service = MagicMock()
            mock_service.find_similar_approaches.return_value = [similar_match]
            MockSimilarityService.return_value = mock_service

            from crabgrass.agents.background.connection import ConnectionAgent

            agent = ConnectionAgent()
            item = mock_queue_item(payload={"approach_id": "app-1", "idea_id": "source-idea"})
            await agent.process_item(item)

            mock_signal.send.assert_called_once()
            call_kwargs = mock_signal.send.call_args[1]
            assert call_kwargs["source_type"] == "approach"

    @pytest.mark.asyncio
    async def test_processes_summary_similarity(self, mock_queue_item, mock_similarity_match):
        """ConnectionAgent should find similar summaries and emit signal."""
        mock_summary = MagicMock()
        mock_summary.embedding = [0.3] * 768
        mock_summary.idea_id = "source-idea"

        similar_match = mock_similarity_match(idea_id="target-idea", similarity=0.75)

        with patch("crabgrass.agents.background.connection.SummaryActions") as mock_summary_actions, \
             patch("crabgrass.agents.background.connection.SimilarityService") as MockSimilarityService, \
             patch("crabgrass.agents.background.connection.agent_found_similarity") as mock_signal:

            mock_summary_actions.get_by_id.return_value = mock_summary

            mock_service = MagicMock()
            mock_service.find_similar_summaries.return_value = [similar_match]
            MockSimilarityService.return_value = mock_service

            from crabgrass.agents.background.connection import ConnectionAgent

            agent = ConnectionAgent()
            item = mock_queue_item(payload={"summary_id": "sum-1", "idea_id": "source-idea"})
            await agent.process_item(item)

            mock_signal.send.assert_called_once()
            call_kwargs = mock_signal.send.call_args[1]
            assert call_kwargs["source_type"] == "summary"

    @pytest.mark.asyncio
    async def test_skips_content_without_embedding(self, mock_queue_item):
        """ConnectionAgent should skip content without embeddings."""
        mock_challenge = MagicMock()
        mock_challenge.embedding = None  # No embedding

        with patch("crabgrass.agents.background.connection.ChallengeActions") as mock_challenge_actions, \
             patch("crabgrass.agents.background.connection.SimilarityService") as MockSimilarityService, \
             patch("crabgrass.agents.background.connection.agent_found_similarity") as mock_signal:

            mock_challenge_actions.get_by_id.return_value = mock_challenge

            from crabgrass.agents.background.connection import ConnectionAgent

            agent = ConnectionAgent()
            item = mock_queue_item(payload={"challenge_id": "chal-1"})
            await agent.process_item(item)

            # Should not search or emit
            MockSimilarityService.return_value.find_similar_challenges.assert_not_called()
            mock_signal.send.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# NurtureAgent Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestNurtureAgent:
    """Tests for NurtureAgent - nurtures nascent ideas."""

    @pytest.mark.asyncio
    async def test_finds_similar_nascent_ideas(self, mock_queue_item, mock_similarity_match):
        """NurtureAgent should find similar nascent ideas."""
        mock_idea = MagicMock()
        mock_idea.id = "nascent-idea"
        mock_idea.title = "Nascent Idea"
        mock_idea.author_id = "user-1"

        mock_summary = MagicMock()
        mock_summary.embedding = [0.1] * 768
        mock_summary.idea_id = "nascent-idea"

        similar_match = mock_similarity_match(idea_id="other-nascent", similarity=0.7)

        with patch("crabgrass.agents.background.nurture.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.nurture.SummaryActions") as mock_summary_actions, \
             patch("crabgrass.agents.background.nurture.ChallengeActions") as mock_challenge_actions, \
             patch("crabgrass.agents.background.nurture.ApproachActions") as mock_approach_actions, \
             patch("crabgrass.agents.background.nurture.ObjectiveActions") as mock_objective_actions, \
             patch("crabgrass.agents.background.nurture.SimilarityService") as MockSimilarityService, \
             patch("crabgrass.agents.background.nurture.QueueActions") as mock_queue_actions:

            mock_idea_actions.get_by_id.return_value = mock_idea
            mock_summary_actions.get_by_idea_id.return_value = mock_summary

            # Both ideas are nascent (no challenge or approach)
            mock_challenge_actions.get_by_idea_id.return_value = None
            mock_approach_actions.get_by_idea_id.return_value = None

            mock_objective_actions.list_active.return_value = []

            mock_service = MagicMock()
            mock_service.find_similar_summaries.return_value = [similar_match]
            MockSimilarityService.return_value = mock_service

            from crabgrass.agents.background.nurture import NurtureAgent

            agent = NurtureAgent()
            item = mock_queue_item(payload={"idea_id": "nascent-idea"})
            await agent.process_item(item)

            # Should have found similar summaries
            mock_service.find_similar_summaries.assert_called_once()

            # Should queue nurture notification
            mock_queue_actions.enqueue.assert_called_once()
            call_args = mock_queue_actions.enqueue.call_args
            assert call_args[1]["queue"].value == "surfacing"
            assert call_args[1]["payload"]["type"] == "nurture_nudge"

    @pytest.mark.asyncio
    async def test_skips_structured_ideas(self, mock_queue_item):
        """NurtureAgent should skip ideas that already have structure (challenge)."""
        mock_challenge = MagicMock()  # Idea has a challenge, not nascent

        with patch("crabgrass.agents.background.nurture.ChallengeActions") as mock_challenge_actions, \
             patch("crabgrass.agents.background.nurture.ApproachActions") as mock_approach_actions, \
             patch("crabgrass.agents.background.nurture.QueueActions") as mock_queue_actions:

            mock_challenge_actions.get_by_idea_id.return_value = mock_challenge
            mock_approach_actions.get_by_idea_id.return_value = None

            from crabgrass.agents.background.nurture import NurtureAgent

            agent = NurtureAgent()
            item = mock_queue_item(payload={"idea_id": "structured-idea"})
            await agent.process_item(item)

            # Should NOT queue any notification
            mock_queue_actions.enqueue.assert_not_called()

    @pytest.mark.asyncio
    async def test_finds_relevant_objectives(self, mock_queue_item):
        """NurtureAgent should find objectives relevant to the idea."""
        mock_idea = MagicMock()
        mock_idea.id = "nascent-idea"
        mock_idea.title = "Nascent Idea"
        mock_idea.author_id = "user-1"

        mock_summary = MagicMock()
        mock_summary.embedding = [0.1] * 768
        mock_summary.idea_id = "nascent-idea"

        # Mock objective with similar embedding
        mock_objective = MagicMock()
        mock_objective.id = "obj-1"
        mock_objective.title = "Relevant Objective"
        mock_objective.embedding = [0.15] * 768  # Similar embedding

        with patch("crabgrass.agents.background.nurture.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.nurture.SummaryActions") as mock_summary_actions, \
             patch("crabgrass.agents.background.nurture.ChallengeActions") as mock_challenge_actions, \
             patch("crabgrass.agents.background.nurture.ApproachActions") as mock_approach_actions, \
             patch("crabgrass.agents.background.nurture.ObjectiveActions") as mock_objective_actions, \
             patch("crabgrass.agents.background.nurture.SimilarityService") as MockSimilarityService, \
             patch("crabgrass.agents.background.nurture.QueueActions") as mock_queue_actions:

            mock_idea_actions.get_by_id.return_value = mock_idea
            mock_summary_actions.get_by_idea_id.return_value = mock_summary

            mock_challenge_actions.get_by_idea_id.return_value = None
            mock_approach_actions.get_by_idea_id.return_value = None

            mock_objective_actions.list_active.return_value = [mock_objective]

            mock_service = MagicMock()
            mock_service.find_similar_summaries.return_value = []  # No similar ideas
            MockSimilarityService.return_value = mock_service

            from crabgrass.agents.background.nurture import NurtureAgent

            agent = NurtureAgent()
            item = mock_queue_item(payload={"idea_id": "nascent-idea"})
            await agent.process_item(item)

            # Should queue nurture notification with objective suggestion
            mock_queue_actions.enqueue.assert_called_once()
            payload = mock_queue_actions.enqueue.call_args[1]["payload"]
            assert len(payload["relevant_objectives"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# ObjectiveAgent Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestObjectiveAgent:
    """Tests for ObjectiveAgent - handles objective retirement."""

    @pytest.mark.asyncio
    async def test_detects_orphaned_ideas(self, mock_queue_item):
        """ObjectiveAgent should detect ideas orphaned by objective retirement."""
        mock_idea = MagicMock()
        mock_idea.id = "orphan-idea"
        mock_idea.title = "Orphan Idea"
        mock_idea.author_id = "user-1"

        mock_summary = MagicMock()
        mock_summary.embedding = [0.1] * 768

        with patch("crabgrass.agents.background.objective.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.objective.IdeaObjectiveActions") as mock_link_actions, \
             patch("crabgrass.agents.background.objective.ObjectiveActions") as mock_objective_actions, \
             patch("crabgrass.agents.background.objective.SummaryActions") as mock_summary_actions, \
             patch("crabgrass.agents.background.objective.agent_flag_orphan") as mock_signal:

            mock_idea_actions.get_by_id.return_value = mock_idea
            mock_link_actions.get_objective_ids_for_idea.return_value = []  # No remaining links
            mock_summary_actions.get_by_idea_id.return_value = mock_summary
            mock_objective_actions.list_active.return_value = []  # No objectives to reconnect to

            from crabgrass.agents.background.objective import ObjectiveAgent

            agent = ObjectiveAgent()
            item = mock_queue_item(payload={
                "idea_id": "orphan-idea",
                "retired_objective_id": "retired-obj",
            })
            await agent.process_item(item)

            # Should emit orphan alert signal
            mock_signal.send.assert_called_once()
            call_kwargs = mock_signal.send.call_args[1]
            assert call_kwargs["idea_id"] == "orphan-idea"
            assert call_kwargs["retired_objective_id"] == "retired-obj"

    @pytest.mark.asyncio
    async def test_suggests_reconnection(self, mock_queue_item):
        """ObjectiveAgent should suggest reconnection when similar objective found."""
        mock_idea = MagicMock()
        mock_idea.id = "orphan-idea"
        mock_idea.title = "Orphan Idea"
        mock_idea.author_id = "user-1"

        mock_summary = MagicMock()
        mock_summary.embedding = [0.1] * 768

        # Similar objective to reconnect to
        mock_objective = MagicMock()
        mock_objective.id = "new-obj"
        mock_objective.title = "New Objective"
        mock_objective.embedding = [0.12] * 768  # Similar embedding

        with patch("crabgrass.agents.background.objective.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.objective.IdeaObjectiveActions") as mock_link_actions, \
             patch("crabgrass.agents.background.objective.ObjectiveActions") as mock_objective_actions, \
             patch("crabgrass.agents.background.objective.SummaryActions") as mock_summary_actions, \
             patch("crabgrass.agents.background.objective.agent_suggest_reconnection") as mock_signal:

            mock_idea_actions.get_by_id.return_value = mock_idea
            mock_link_actions.get_objective_ids_for_idea.return_value = []
            mock_summary_actions.get_by_idea_id.return_value = mock_summary
            mock_objective_actions.list_active.return_value = [mock_objective]

            from crabgrass.agents.background.objective import ObjectiveAgent

            agent = ObjectiveAgent()
            item = mock_queue_item(payload={
                "idea_id": "orphan-idea",
                "retired_objective_id": "retired-obj",
            })
            await agent.process_item(item)

            # Should emit reconnection suggestion signal
            mock_signal.send.assert_called_once()
            call_kwargs = mock_signal.send.call_args[1]
            assert call_kwargs["idea_id"] == "orphan-idea"
            assert call_kwargs["suggested_objective_id"] == "new-obj"

    @pytest.mark.asyncio
    async def test_skips_ideas_with_active_links(self, mock_queue_item):
        """ObjectiveAgent should skip ideas that still have active objective links."""
        mock_idea = MagicMock()
        mock_idea.id = "linked-idea"

        mock_objective = MagicMock()
        mock_objective.status = "Active"

        with patch("crabgrass.agents.background.objective.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.objective.IdeaObjectiveActions") as mock_link_actions, \
             patch("crabgrass.agents.background.objective.ObjectiveActions") as mock_objective_actions, \
             patch("crabgrass.agents.background.objective.agent_flag_orphan") as mock_orphan_signal, \
             patch("crabgrass.agents.background.objective.agent_suggest_reconnection") as mock_reconnect_signal:

            mock_idea_actions.get_by_id.return_value = mock_idea
            mock_link_actions.get_objective_ids_for_idea.return_value = ["other-obj"]
            mock_objective_actions.get_by_id.return_value = mock_objective

            from crabgrass.agents.background.objective import ObjectiveAgent

            agent = ObjectiveAgent()
            item = mock_queue_item(payload={
                "idea_id": "linked-idea",
                "retired_objective_id": "retired-obj",
            })
            await agent.process_item(item)

            # Should NOT emit any signals
            mock_orphan_signal.send.assert_not_called()
            mock_reconnect_signal.send.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# SurfacingAgent Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestSurfacingAgent:
    """Tests for SurfacingAgent - creates notifications from queue events."""

    @pytest.mark.asyncio
    async def test_handles_idea_linked_event(self, mock_queue_item):
        """SurfacingAgent should create notifications when idea linked to objective."""
        mock_idea = MagicMock()
        mock_idea.id = "idea-1"
        mock_idea.title = "New Idea"
        mock_idea.author_id = "user-1"

        mock_objective = MagicMock()
        mock_objective.id = "obj-1"
        mock_objective.title = "Team Objective"

        with patch("crabgrass.agents.background.surfacing.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.surfacing.ObjectiveActions") as mock_objective_actions, \
             patch("crabgrass.agents.background.surfacing.WatchActions") as mock_watch_actions, \
             patch("crabgrass.agents.background.surfacing.NotificationActions") as mock_notification_actions:

            mock_idea_actions.get_by_id.return_value = mock_idea
            mock_objective_actions.get_by_id.return_value = mock_objective
            mock_watch_actions.get_objective_watchers.return_value = ["user-2", "user-3"]

            from crabgrass.agents.background.surfacing import SurfacingAgent

            agent = SurfacingAgent()
            item = mock_queue_item(payload={
                "type": "idea_linked",
                "idea_id": "idea-1",
                "objective_id": "obj-1",
            })
            await agent.process_item(item)

            # Should create notifications for watchers (excluding author)
            assert mock_notification_actions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_similar_found_event(self, mock_queue_item):
        """SurfacingAgent should notify user when similar content found."""
        mock_source_idea = MagicMock()
        mock_source_idea.id = "source-idea"
        mock_source_idea.title = "Source Idea"
        mock_source_idea.author_id = "user-1"

        mock_target_idea = MagicMock()
        mock_target_idea.id = "target-idea"
        mock_target_idea.title = "Similar Target"

        with patch("crabgrass.agents.background.surfacing.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.surfacing.NotificationActions") as mock_notification_actions:

            mock_idea_actions.get_by_id.side_effect = lambda id: {
                "source-idea": mock_source_idea,
                "target-idea": mock_target_idea,
            }.get(id)

            from crabgrass.agents.background.surfacing import SurfacingAgent

            agent = SurfacingAgent()
            item = mock_queue_item(payload={
                "type": "similar_found",
                "source_idea_id": "source-idea",
                "target_idea_id": "target-idea",
                "similarity_score": 0.85,
            })
            await agent.process_item(item)

            # Should notify the source idea author
            mock_notification_actions.create.assert_called_once()
            call_kwargs = mock_notification_actions.create.call_args[1]
            assert call_kwargs["user_id"] == "user-1"
            assert "85%" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_handles_orphan_alert_event(self, mock_queue_item):
        """SurfacingAgent should alert user when idea becomes orphaned."""
        mock_idea = MagicMock()
        mock_idea.id = "orphan-idea"
        mock_idea.title = "Orphan Idea"
        mock_idea.author_id = "user-1"

        with patch("crabgrass.agents.background.surfacing.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.surfacing.NotificationActions") as mock_notification_actions:

            mock_idea_actions.get_by_id.return_value = mock_idea

            from crabgrass.agents.background.surfacing import SurfacingAgent

            agent = SurfacingAgent()
            item = mock_queue_item(payload={
                "type": "orphan_alert",
                "idea_id": "orphan-idea",
                "retired_objective_id": "retired-obj",
            })
            await agent.process_item(item)

            # Should notify the idea author
            mock_notification_actions.create.assert_called_once()
            call_kwargs = mock_notification_actions.create.call_args[1]
            assert call_kwargs["user_id"] == "user-1"
            assert "no longer linked" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_handles_reconnection_suggestion_event(self, mock_queue_item):
        """SurfacingAgent should suggest reconnection to author."""
        mock_idea = MagicMock()
        mock_idea.id = "orphan-idea"
        mock_idea.title = "Orphan Idea"
        mock_idea.author_id = "user-1"

        mock_objective = MagicMock()
        mock_objective.id = "new-obj"
        mock_objective.title = "New Objective"

        with patch("crabgrass.agents.background.surfacing.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.surfacing.ObjectiveActions") as mock_objective_actions, \
             patch("crabgrass.agents.background.surfacing.NotificationActions") as mock_notification_actions:

            mock_idea_actions.get_by_id.return_value = mock_idea
            mock_objective_actions.get_by_id.return_value = mock_objective

            from crabgrass.agents.background.surfacing import SurfacingAgent

            agent = SurfacingAgent()
            item = mock_queue_item(payload={
                "type": "reconnection_suggestion",
                "idea_id": "orphan-idea",
                "suggested_objective_id": "new-obj",
                "similarity_score": 0.65,
            })
            await agent.process_item(item)

            # Should notify the idea author with suggestion
            mock_notification_actions.create.assert_called_once()
            call_kwargs = mock_notification_actions.create.call_args[1]
            assert call_kwargs["user_id"] == "user-1"
            assert "New Objective" in call_kwargs["message"]
            assert "65%" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_handles_nurture_nudge_event(self, mock_queue_item):
        """SurfacingAgent should create nurture notification."""
        with patch("crabgrass.agents.background.surfacing.NotificationActions") as mock_notification_actions:

            from crabgrass.agents.background.surfacing import SurfacingAgent

            agent = SurfacingAgent()
            item = mock_queue_item(payload={
                "type": "nurture_nudge",
                "idea_id": "idea-1",
                "author_id": "user-1",
                "message": "Found 2 similar ideas you might want to collaborate on",
            })
            await agent.process_item(item)

            # Should create notification with pre-built message
            mock_notification_actions.create.assert_called_once()
            call_kwargs = mock_notification_actions.create.call_args[1]
            assert call_kwargs["user_id"] == "user-1"
            assert "collaborate" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_excludes_author_from_own_notifications(self, mock_queue_item):
        """SurfacingAgent should not notify authors of their own actions."""
        mock_idea = MagicMock()
        mock_idea.id = "idea-1"
        mock_idea.title = "New Idea"
        mock_idea.author_id = "user-1"  # Author is watching too

        mock_objective = MagicMock()
        mock_objective.id = "obj-1"
        mock_objective.title = "Team Objective"

        with patch("crabgrass.agents.background.surfacing.IdeaActions") as mock_idea_actions, \
             patch("crabgrass.agents.background.surfacing.ObjectiveActions") as mock_objective_actions, \
             patch("crabgrass.agents.background.surfacing.WatchActions") as mock_watch_actions, \
             patch("crabgrass.agents.background.surfacing.NotificationActions") as mock_notification_actions:

            mock_idea_actions.get_by_id.return_value = mock_idea
            mock_objective_actions.get_by_id.return_value = mock_objective
            # Author is one of the watchers
            mock_watch_actions.get_objective_watchers.return_value = ["user-1", "user-2"]

            from crabgrass.agents.background.surfacing import SurfacingAgent

            agent = SurfacingAgent()
            item = mock_queue_item(payload={
                "type": "idea_linked",
                "idea_id": "idea-1",
                "objective_id": "obj-1",
            })
            await agent.process_item(item)

            # Should only notify user-2 (not user-1 who is the author)
            assert mock_notification_actions.create.call_count == 1
            call_kwargs = mock_notification_actions.create.call_args[1]
            assert call_kwargs["user_id"] == "user-2"

    @pytest.mark.asyncio
    async def test_handles_unknown_event_type(self, mock_queue_item, caplog):
        """SurfacingAgent should log warning for unknown event types."""
        import logging
        caplog.set_level(logging.WARNING)

        from crabgrass.agents.background.surfacing import SurfacingAgent

        agent = SurfacingAgent()
        item = mock_queue_item(payload={
            "type": "unknown_event_type",
        })
        await agent.process_item(item)

        # Should log warning about unknown type
        assert any("unknown" in record.message.lower() for record in caplog.records)


# ─────────────────────────────────────────────────────────────────────────────
# BackgroundAgent Base Class Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestBackgroundAgentBase:
    """Tests for the BackgroundAgent base class."""

    @pytest.mark.asyncio
    async def test_run_once_completes_items(self, test_db):
        """run_once should mark items complete after successful processing."""
        from crabgrass.concepts.queue import QueueActions, QueueName, QueueItemStatus
        from crabgrass.agents.runner import BackgroundAgent

        # Create test agent
        class TestAgent(BackgroundAgent):
            def __init__(self):
                super().__init__(QueueName.CONNECTION)
                self.processed_ids = []

            async def process_item(self, item):
                self.processed_ids.append(item.id)

        # Enqueue test item
        QueueActions.enqueue(QueueName.CONNECTION, {"test": "data"})

        agent = TestAgent()
        processed = await agent.run_once(batch_size=10)

        assert processed == 1
        assert len(agent.processed_ids) == 1

        # Item should be completed
        counts = QueueActions.count_by_status(QueueName.CONNECTION)
        assert counts.get(QueueItemStatus.COMPLETED.value, 0) == 1

    @pytest.mark.asyncio
    async def test_run_once_fails_items_on_error(self, test_db):
        """run_once should mark items failed on processing error."""
        from crabgrass.concepts.queue import QueueActions, QueueName, QueueItemStatus
        from crabgrass.agents.runner import BackgroundAgent

        class FailingAgent(BackgroundAgent):
            def __init__(self):
                super().__init__(QueueName.NURTURE)

            async def process_item(self, item):
                raise Exception("Processing failed!")

        # Enqueue test item
        QueueActions.enqueue(QueueName.NURTURE, {"test": "data"})

        agent = FailingAgent()
        processed = await agent.run_once(batch_size=10)

        # Item processed but failed
        assert processed == 0

        # Item should be marked failed
        counts = QueueActions.count_by_status(QueueName.NURTURE)
        assert counts.get(QueueItemStatus.FAILED.value, 0) == 1

    @pytest.mark.asyncio
    async def test_run_once_returns_zero_when_empty(self, test_db):
        """run_once should return 0 when queue is empty."""
        from crabgrass.concepts.queue import QueueName
        from crabgrass.agents.runner import BackgroundAgent

        class TestAgent(BackgroundAgent):
            def __init__(self):
                super().__init__(QueueName.SURFACING)

            async def process_item(self, item):
                pass

        agent = TestAgent()
        processed = await agent.run_once(batch_size=10)

        assert processed == 0


# ─────────────────────────────────────────────────────────────────────────────
# Integration-style Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestAgentQueueIntegration:
    """Integration tests for agents with real queue operations."""

    @pytest.mark.asyncio
    async def test_connection_agent_queue_flow(self, test_db, mock_embedding_service):
        """ConnectionAgent should process queue items end-to-end."""
        from crabgrass.concepts.queue import QueueActions, QueueName, QueueItemStatus
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.challenge import ChallengeActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.agents.background.connection import ConnectionAgent

        # Setup: Create user and ideas
        UserActions.ensure_mock_users_exist()
        idea = IdeaActions.create(title="Test Idea", author_id="sarah-001")
        ChallengeActions.create(idea_id=idea.id, content="Test challenge content")

        # Enqueue connection analysis
        QueueActions.enqueue(QueueName.CONNECTION, {
            "challenge_id": "nonexistent",  # Will be skipped gracefully
            "idea_id": idea.id,
        })

        # Process
        agent = ConnectionAgent()
        processed = await agent.run_once()

        # Should have processed at least 1 item (may have more from other tests)
        counts = QueueActions.count_by_status(QueueName.CONNECTION)
        assert counts.get(QueueItemStatus.COMPLETED.value, 0) >= 1

    @pytest.mark.asyncio
    async def test_surfacing_agent_creates_notifications(self, test_db, mock_embedding_service):
        """SurfacingAgent should create real notifications."""
        from crabgrass.concepts.queue import QueueActions, QueueName
        from crabgrass.concepts.notification import NotificationActions
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.objective import ObjectiveActions
        from crabgrass.concepts.watch import WatchActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.agents.background.surfacing import SurfacingAgent

        # Setup
        UserActions.ensure_mock_users_exist()
        idea = IdeaActions.create(title="Linked Idea", author_id="sarah-001")
        objective = ObjectiveActions.create(
            title="Team Goal",
            description="A shared team goal",
            author_id="sarah-001",
        )

        # Add watcher (different user)
        WatchActions.create(user_id="mike-001", target_type="objective", target_id=objective.id)

        # Enqueue surfacing event
        QueueActions.enqueue(QueueName.SURFACING, {
            "type": "idea_linked",
            "idea_id": idea.id,
            "objective_id": objective.id,
        })

        # Process
        agent = SurfacingAgent()
        await agent.run_once()

        # Should have created notification for mike
        notifications = NotificationActions.list_for_user("mike-001")
        assert len(notifications) == 1
        assert "Linked Idea" in notifications[0].message
        assert "Team Goal" in notifications[0].message
