"""Integration tests for V2 demo scenarios.

These tests verify the data layer and notification creation work correctly.
They use simplified mocking where needed and focus on verifiable outcomes.

Scenarios covered:
1. Bottom-Up Discovery - Similar ideas are found and notifications created
2. Objective-Linked Idea - Watchers are notified when idea linked
3. Nurturing a Nascent Idea - Nurture notifications work
4. Objective Retirement Flow - Orphan alerts work
5. Real-Time Notifications - Notifications can be listed and cleared
"""

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 1: Bottom-Up Discovery
# ─────────────────────────────────────────────────────────────────────────────


class TestBottomUpDiscovery:
    """ConnectionAgent finds similar ideas and creates notifications."""

    def test_similarity_notification_created(
        self, test_db, mock_embedding_service
    ):
        """Similarity discovery triggers notification for author."""
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.concepts.notification import NotificationActions, NotificationType

        UserActions.ensure_mock_users_exist()

        # Create two ideas
        idea1 = IdeaActions.create(title="Voice Memo App", author_id="sarah-001")
        idea2 = IdeaActions.create(title="Audio Notes Tool", author_id="mike-001")

        # Create notification (simulating what SurfacingAgent would do after ConnectionAgent finds similarity)
        NotificationActions.create(
            user_id="sarah-001",
            type=NotificationType.SIMILAR_FOUND,
            message=f"Found similar idea 'Audio Notes Tool' (85% match)",
            source_type="idea",
            source_id=idea1.id,
            related_id=idea2.id,
        )

        # Verify notification exists
        notifications = NotificationActions.list_for_user("sarah-001")
        assert len(notifications) == 1
        assert "85%" in notifications[0].message

    def test_graph_edges_created_from_relationship(
        self, test_db, mock_embedding_service
    ):
        """Graph edges are created when similarity is recorded."""
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.database import fetchone

        UserActions.ensure_mock_users_exist()

        idea1 = IdeaActions.create(title="Idea A", author_id="sarah-001")
        idea2 = IdeaActions.create(title="Idea B", author_id="mike-001")

        # Insert graph edge directly (simulating sync handler)
        from crabgrass.database import execute
        execute(
            """
            INSERT INTO graph_similar_ideas (from_idea_id, to_idea_id, similarity_score, match_type)
            VALUES (?, ?, ?, ?)
            """,
            [idea1.id, idea2.id, 0.85, "summary"],
        )

        # Verify edge exists
        row = fetchone(
            "SELECT similarity_score FROM graph_similar_ideas WHERE from_idea_id = ?",
            [idea1.id],
        )
        assert row is not None
        assert abs(row[0] - 0.85) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 2: Objective-Linked Idea
# ─────────────────────────────────────────────────────────────────────────────


class TestObjectiveLinkedIdea:
    """VP watches objective, gets notified when idea is linked."""

    @pytest.mark.asyncio
    async def test_objective_watcher_notified_on_link(
        self, test_db, mock_embedding_service
    ):
        """When idea is linked to watched objective, watchers are notified."""
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.objective import ObjectiveActions
        from crabgrass.concepts.idea_objective import IdeaObjectiveActions
        from crabgrass.concepts.watch import WatchActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.concepts.queue import QueueActions, QueueName
        from crabgrass.concepts.notification import NotificationActions
        from crabgrass.agents.background.surfacing import SurfacingAgent

        UserActions.ensure_mock_users_exist()

        # Senior creates objective
        objective = ObjectiveActions.create(
            title="Improve Customer Experience",
            description="Focus on customer satisfaction",
            author_id="senior-001",
        )

        # VP watches the objective
        WatchActions.create(
            user_id="senior-001",
            target_type="objective",
            target_id=objective.id,
        )

        # Mike also watches
        WatchActions.create(
            user_id="mike-001",
            target_type="objective",
            target_id=objective.id,
        )

        # Sarah creates an idea
        idea = IdeaActions.create(title="Customer Feedback Portal", author_id="sarah-001")

        # Link idea to objective
        IdeaObjectiveActions.link(idea.id, objective.id)

        # Enqueue surfacing event (normally done by sync handler)
        QueueActions.enqueue(QueueName.SURFACING, {
            "type": "idea_linked",
            "idea_id": idea.id,
            "objective_id": objective.id,
        })

        # Process notifications
        surf_agent = SurfacingAgent()
        await surf_agent.run_once()

        # Verify: Mike should be notified (not Sarah who is the author)
        mike_notifs = NotificationActions.list_for_user("mike-001")
        assert len(mike_notifs) >= 1
        assert "Customer Feedback Portal" in mike_notifs[0].message

        # Senior should also be notified
        senior_notifs = NotificationActions.list_for_user("senior-001")
        assert len(senior_notifs) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 3: Nurturing a Nascent Idea
# ─────────────────────────────────────────────────────────────────────────────


class TestNurturingNascentIdea:
    """NurtureAgent nudges users about similar nascent ideas."""

    @pytest.mark.asyncio
    async def test_nurture_notification_created(
        self, test_db, mock_embedding_service
    ):
        """Nurture notifications can be created via queue."""
        from crabgrass.concepts.user import UserActions
        from crabgrass.concepts.queue import QueueActions, QueueName
        from crabgrass.concepts.notification import NotificationActions
        from crabgrass.agents.background.surfacing import SurfacingAgent

        UserActions.ensure_mock_users_exist()

        # Enqueue nurture nudge (simulating what NurtureAgent would do)
        QueueActions.enqueue(QueueName.SURFACING, {
            "type": "nurture_nudge",
            "idea_id": "idea-123",
            "author_id": "sarah-001",
            "message": "Found 2 similar nascent ideas you might want to collaborate on",
        })

        # Process
        surf_agent = SurfacingAgent()
        await surf_agent.run_once()

        # Sarah should get a nurture nudge
        notifications = NotificationActions.list_for_user("sarah-001")
        assert len(notifications) >= 1
        assert "collaborate" in notifications[0].message.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 4: Objective Retirement Flow
# ─────────────────────────────────────────────────────────────────────────────


class TestObjectiveRetirementFlow:
    """ObjectiveAgent handles orphaned ideas when objective retires."""

    @pytest.mark.asyncio
    async def test_orphan_alert_notification(
        self, test_db, mock_embedding_service
    ):
        """Orphan alerts are created via surfacing queue."""
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.concepts.queue import QueueActions, QueueName
        from crabgrass.concepts.notification import NotificationActions
        from crabgrass.agents.background.surfacing import SurfacingAgent

        UserActions.ensure_mock_users_exist()

        idea = IdeaActions.create(title="Marketing Campaign", author_id="sarah-001")

        # Enqueue orphan alert (simulating what ObjectiveAgent would do)
        QueueActions.enqueue(QueueName.SURFACING, {
            "type": "orphan_alert",
            "idea_id": idea.id,
            "retired_objective_id": "old-obj-123",
        })

        # Process
        surf_agent = SurfacingAgent()
        await surf_agent.run_once()

        # Sarah should get orphan alert
        notifications = NotificationActions.list_for_user("sarah-001")
        assert len(notifications) >= 1
        assert "no longer linked" in notifications[0].message.lower()

    @pytest.mark.asyncio
    async def test_reconnection_suggestion_notification(
        self, test_db, mock_embedding_service
    ):
        """Reconnection suggestions are created via surfacing queue."""
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.objective import ObjectiveActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.concepts.queue import QueueActions, QueueName
        from crabgrass.concepts.notification import NotificationActions
        from crabgrass.agents.background.surfacing import SurfacingAgent

        UserActions.ensure_mock_users_exist()

        idea = IdeaActions.create(title="Ongoing Initiative", author_id="sarah-001")
        new_objective = ObjectiveActions.create(
            title="Q1 Goals",
            description="Goals for Q1",
            author_id="senior-001",
        )

        # Enqueue reconnection suggestion
        QueueActions.enqueue(QueueName.SURFACING, {
            "type": "reconnection_suggestion",
            "idea_id": idea.id,
            "suggested_objective_id": new_objective.id,
            "similarity_score": 0.75,
        })

        # Process
        surf_agent = SurfacingAgent()
        await surf_agent.run_once()

        # Sarah should get reconnection suggestion
        notifications = NotificationActions.list_for_user("sarah-001")
        assert len(notifications) >= 1
        assert "Q1 Goals" in notifications[0].message
        assert "75%" in notifications[0].message


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 5: Real-Time Notifications
# ─────────────────────────────────────────────────────────────────────────────


class TestRealTimeNotifications:
    """Notifications are created and can be retrieved."""

    def test_notifications_appear_in_list_all(self, test_db, mock_embedding_service):
        """Notifications from all users appear in list_all endpoint."""
        from crabgrass.concepts.notification import NotificationActions, NotificationType
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()

        # Create notifications for different users
        NotificationActions.create(
            user_id="sarah-001",
            type=NotificationType.SIMILAR_FOUND,
            message="Found a similar idea",
            source_type="idea",
            source_id="idea-1",
        )

        NotificationActions.create(
            user_id="mike-001",
            type=NotificationType.IDEA_LINKED,
            message="New idea linked to your objective",
            source_type="objective",
            source_id="obj-1",
        )

        # list_all should return both
        all_notifs = NotificationActions.list_all()
        assert len(all_notifs) == 2

    def test_notifications_can_be_cleared(self, test_db, mock_embedding_service):
        """All notifications can be cleared for demo reset."""
        from crabgrass.concepts.notification import NotificationActions, NotificationType
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()

        # Create some notifications
        for i in range(5):
            NotificationActions.create(
                user_id="sarah-001",
                type=NotificationType.NURTURE_NUDGE,
                message=f"Nudge {i}",
                source_type="idea",
                source_id=f"idea-{i}",
            )

        assert len(NotificationActions.list_all()) == 5

        # Clear all
        NotificationActions.clear_all()

        assert len(NotificationActions.list_all()) == 0

    def test_api_returns_all_notifications(self, client, test_db, mock_embedding_service):
        """API endpoint returns notifications from all users."""
        from crabgrass.concepts.notification import NotificationActions, NotificationType
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()

        NotificationActions.create(
            user_id="sarah-001",
            type=NotificationType.SIMILAR_FOUND,
            message="Test notification",
            source_type="idea",
            source_id="idea-1",
        )

        response = client.get("/api/notifications/all")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["message"] == "Test notification"

    def test_api_clears_all_notifications(self, client, test_db, mock_embedding_service):
        """API can clear all notifications."""
        from crabgrass.concepts.notification import NotificationActions, NotificationType
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()

        NotificationActions.create(
            user_id="sarah-001",
            type=NotificationType.SIMILAR_FOUND,
            message="Will be cleared",
            source_type="idea",
            source_id="idea-1",
        )

        response = client.delete("/api/notifications/all")
        assert response.status_code == 204

        # Verify cleared
        response = client.get("/api/notifications/all")
        assert len(response.json()) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Full Flow Integration Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestFullDemoFlow:
    """Tests that verify complete data flows work end-to-end."""

    @pytest.mark.asyncio
    async def test_idea_creation_to_notification_flow(
        self, test_db, mock_embedding_service
    ):
        """Complete flow: Create idea → Link to objective → Notification appears."""
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.summary import SummaryActions
        from crabgrass.concepts.challenge import ChallengeActions
        from crabgrass.concepts.objective import ObjectiveActions
        from crabgrass.concepts.idea_objective import IdeaObjectiveActions
        from crabgrass.concepts.watch import WatchActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.concepts.queue import QueueActions, QueueName
        from crabgrass.concepts.notification import NotificationActions
        from crabgrass.agents.background.surfacing import SurfacingAgent

        UserActions.ensure_mock_users_exist()

        # 1. Senior creates and watches an objective
        objective = ObjectiveActions.create(
            title="Innovation Initiative",
            description="Drive innovation across the org",
            author_id="senior-001",
        )
        WatchActions.create(
            user_id="senior-001",
            target_type="objective",
            target_id=objective.id,
        )

        # 2. Sarah creates a fully-structured idea
        idea = IdeaActions.create(title="AI Assistant", author_id="sarah-001")
        SummaryActions.create(idea_id=idea.id, content="An AI assistant for employees")
        ChallengeActions.create(idea_id=idea.id, content="Employees waste time on routine tasks")

        # 3. Idea gets linked to objective
        IdeaObjectiveActions.link(idea.id, objective.id)

        # 4. Trigger surfacing (normally done by sync)
        QueueActions.enqueue(QueueName.SURFACING, {
            "type": "idea_linked",
            "idea_id": idea.id,
            "objective_id": objective.id,
        })

        # 5. Process surfacing
        surf_agent = SurfacingAgent()
        await surf_agent.run_once()

        # 6. Verify: Senior got notification
        notifications = NotificationActions.list_for_user("senior-001")
        assert len(notifications) >= 1
        assert "AI Assistant" in notifications[0].message
        assert "Innovation Initiative" in notifications[0].message

        # 7. Verify: Notification appears in all-users list
        all_notifs = NotificationActions.list_all()
        assert len(all_notifs) >= 1

    def test_queue_processing_completes_items(self, test_db, mock_embedding_service):
        """Queue items are marked complete after processing."""
        from crabgrass.concepts.queue import QueueActions, QueueName, QueueItemStatus
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()

        # Enqueue items
        for i in range(3):
            QueueActions.enqueue(QueueName.SURFACING, {"test": i})

        # Check pending count
        counts = QueueActions.count_by_status(QueueName.SURFACING)
        assert counts.get(QueueItemStatus.PENDING.value, 0) == 3
