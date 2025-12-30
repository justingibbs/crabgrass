"""Tests for Notifications API endpoints."""

import pytest
from crabgrass.concepts.notification import NotificationActions, NotificationType
from crabgrass.concepts.user import UserActions


class TestListNotifications:
    """Tests for GET /api/notifications."""

    def test_list_notifications_empty(self, authenticated_client):
        """List returns empty when no notifications exist."""
        response = authenticated_client.get("/api/notifications")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_notifications_returns_created(self, authenticated_client, test_db):
        """List returns notifications after creation."""
        # Create a notification directly
        current_user = UserActions.get_current()
        NotificationActions.create(
            user_id=current_user.id,
            type=NotificationType.SIMILAR_FOUND,
            message="Found similar idea",
            source_type="idea",
            source_id="idea-123",
        )

        response = authenticated_client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "similar_found"
        assert data[0]["message"] == "Found similar idea"

    def test_list_notifications_unread_only(self, authenticated_client, test_db):
        """List respects unread_only filter."""
        current_user = UserActions.get_current()

        # Create read and unread notifications
        n1 = NotificationActions.create(
            user_id=current_user.id,
            type=NotificationType.SIMILAR_FOUND,
            message="Unread notification",
            source_type="idea",
            source_id="idea-123",
        )

        n2 = NotificationActions.create(
            user_id=current_user.id,
            type=NotificationType.IDEA_LINKED,
            message="Read notification",
            source_type="idea",
            source_id="idea-456",
        )
        NotificationActions.mark_read(n2.id)

        # All notifications
        response = authenticated_client.get("/api/notifications")
        assert len(response.json()) == 2

        # Only unread
        response = authenticated_client.get("/api/notifications?unread_only=true")
        assert len(response.json()) == 1
        assert response.json()[0]["message"] == "Unread notification"


class TestNotificationCount:
    """Tests for GET /api/notifications/count."""

    def test_count_returns_zero_when_empty(self, authenticated_client):
        """Count returns 0 when no notifications."""
        response = authenticated_client.get("/api/notifications/count")
        assert response.status_code == 200
        assert response.json()["unread_count"] == 0

    def test_count_returns_unread_count(self, authenticated_client, test_db):
        """Count returns number of unread notifications."""
        current_user = UserActions.get_current()

        # Create 3 notifications, mark 1 as read
        for i in range(3):
            NotificationActions.create(
                user_id=current_user.id,
                type=NotificationType.NURTURE_NUDGE,
                message=f"Notification {i}",
                source_type="idea",
                source_id=f"idea-{i}",
            )

        # Mark one as read
        notifications = NotificationActions.list_for_user(current_user.id)
        NotificationActions.mark_read(notifications[0].id)

        response = authenticated_client.get("/api/notifications/count")
        assert response.json()["unread_count"] == 2


class TestMarkNotificationRead:
    """Tests for POST /api/notifications/{id}/read."""

    def test_mark_notification_read(self, authenticated_client, test_db):
        """Can mark notification as read."""
        current_user = UserActions.get_current()

        notification = NotificationActions.create(
            user_id=current_user.id,
            type=NotificationType.CONTRIBUTION,
            message="Someone contributed",
            source_type="idea",
            source_id="idea-123",
        )

        response = authenticated_client.post(f"/api/notifications/{notification.id}/read")
        assert response.status_code == 200
        assert response.json()["read"] is True

    def test_mark_notification_read_not_found(self, authenticated_client):
        """Returns 404 for nonexistent notification."""
        response = authenticated_client.post("/api/notifications/nonexistent-id/read")
        assert response.status_code == 404


class TestMarkAllRead:
    """Tests for POST /api/notifications/read-all."""

    def test_mark_all_read(self, authenticated_client, test_db):
        """Can mark all notifications as read."""
        current_user = UserActions.get_current()

        # Create multiple notifications
        for i in range(3):
            NotificationActions.create(
                user_id=current_user.id,
                type=NotificationType.NURTURE_NUDGE,
                message=f"Notification {i}",
                source_type="idea",
                source_id=f"idea-{i}",
            )

        response = authenticated_client.post("/api/notifications/read-all")
        assert response.status_code == 200
        assert response.json()["marked_read"] == 3

        # Verify all are read
        count_resp = authenticated_client.get("/api/notifications/count")
        assert count_resp.json()["unread_count"] == 0


class TestDeleteNotification:
    """Tests for DELETE /api/notifications/{id}."""

    def test_delete_notification(self, authenticated_client, test_db):
        """Can delete a notification."""
        current_user = UserActions.get_current()

        notification = NotificationActions.create(
            user_id=current_user.id,
            type=NotificationType.ORPHAN_ALERT,
            message="Orphaned idea alert",
            source_type="idea",
            source_id="idea-123",
        )

        response = authenticated_client.delete(f"/api/notifications/{notification.id}")
        assert response.status_code == 204

        # Verify deleted
        list_resp = authenticated_client.get("/api/notifications")
        assert len(list_resp.json()) == 0

    def test_delete_notification_not_found(self, authenticated_client):
        """Returns 404 for nonexistent notification."""
        response = authenticated_client.delete("/api/notifications/nonexistent-id")
        assert response.status_code == 404
