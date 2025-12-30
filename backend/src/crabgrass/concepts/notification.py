"""Notification concept - alerts for users.

Notifications are created by background agents when events occur
that a user should know about.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4

from crabgrass.database import execute, fetchone, fetchall


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────


class NotificationType(str, Enum):
    """Types of notifications."""

    SIMILAR_FOUND = "similar_found"
    IDEA_LINKED = "idea_linked"
    OBJECTIVE_RETIRED = "objective_retired"
    NURTURE_NUDGE = "nurture_nudge"
    CONTRIBUTION = "contribution"
    ORPHAN_ALERT = "orphan_alert"
    RECONNECTION_SUGGESTION = "reconnection_suggestion"


@dataclass
class Notification:
    """An alert for a user."""

    id: str
    user_id: str
    type: NotificationType
    message: str
    source_type: str  # "idea", "objective", "summary", etc.
    source_id: str
    related_id: str | None = None  # Optional related entity
    read: bool = False
    created_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class NotificationActions:
    """Actions for the Notification concept."""

    @staticmethod
    def create(
        user_id: str,
        type: NotificationType,
        message: str,
        source_type: str,
        source_id: str,
        related_id: str | None = None,
    ) -> Notification:
        """Create a notification for a user."""
        notification_id = str(uuid4())
        now = datetime.utcnow()

        # Convert enum to string for storage
        type_str = type.value if isinstance(type, NotificationType) else type

        execute(
            """
            INSERT INTO notifications (id, user_id, type, message, source_type, source_id, related_id, read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [notification_id, user_id, type_str, message, source_type, source_id, related_id, False, now],
        )

        return Notification(
            id=notification_id,
            user_id=user_id,
            type=type if isinstance(type, NotificationType) else NotificationType(type),
            message=message,
            source_type=source_type,
            source_id=source_id,
            related_id=related_id,
            read=False,
            created_at=now,
        )

    @staticmethod
    def get_by_id(notification_id: str) -> Notification | None:
        """Get a notification by ID."""
        row = fetchone(
            """
            SELECT id, user_id, type, message, source_type, source_id, related_id, read, created_at
            FROM notifications WHERE id = ?
            """,
            [notification_id],
        )
        if row:
            return Notification(
                id=row[0],
                user_id=row[1],
                type=NotificationType(row[2]),
                message=row[3],
                source_type=row[4],
                source_id=row[5],
                related_id=row[6],
                read=row[7],
                created_at=row[8],
            )
        return None

    @staticmethod
    def list_for_user(
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        """List notifications for a user."""
        if unread_only:
            rows = fetchall(
                """
                SELECT id, user_id, type, message, source_type, source_id, related_id, read, created_at
                FROM notifications
                WHERE user_id = ? AND read = FALSE
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [user_id, limit],
            )
        else:
            rows = fetchall(
                """
                SELECT id, user_id, type, message, source_type, source_id, related_id, read, created_at
                FROM notifications
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [user_id, limit],
            )

        return [
            Notification(
                id=row[0],
                user_id=row[1],
                type=NotificationType(row[2]),
                message=row[3],
                source_type=row[4],
                source_id=row[5],
                related_id=row[6],
                read=row[7],
                created_at=row[8],
            )
            for row in rows
        ]

    @staticmethod
    def count_unread(user_id: str) -> int:
        """Count unread notifications for a user."""
        row = fetchone(
            """
            SELECT COUNT(*)
            FROM notifications
            WHERE user_id = ? AND read = FALSE
            """,
            [user_id],
        )
        return row[0] if row else 0

    @staticmethod
    def mark_read(notification_id: str) -> Notification | None:
        """Mark a notification as read."""
        notification = NotificationActions.get_by_id(notification_id)
        if not notification:
            return None

        execute(
            "UPDATE notifications SET read = TRUE WHERE id = ?",
            [notification_id],
        )

        notification.read = True
        return notification

    @staticmethod
    def mark_all_read(user_id: str) -> int:
        """Mark all notifications as read for a user.

        Returns count of notifications marked as read.
        """
        row = fetchone(
            """
            SELECT COUNT(*)
            FROM notifications
            WHERE user_id = ? AND read = FALSE
            """,
            [user_id],
        )
        count = row[0] if row else 0

        if count > 0:
            execute(
                "UPDATE notifications SET read = TRUE WHERE user_id = ? AND read = FALSE",
                [user_id],
            )

        return count

    @staticmethod
    def delete(notification_id: str) -> bool:
        """Delete a notification."""
        notification = NotificationActions.get_by_id(notification_id)
        if not notification:
            return False

        execute(
            "DELETE FROM notifications WHERE id = ?",
            [notification_id],
        )

        return True

    @staticmethod
    def delete_old(days: int = 30) -> int:
        """Delete notifications older than specified days.

        Returns count of deleted notifications.
        """
        row = fetchone(
            """
            SELECT COUNT(*)
            FROM notifications
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL ? DAY
            """,
            [days],
        )
        count = row[0] if row else 0

        if count > 0:
            execute(
                """
                DELETE FROM notifications
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL ? DAY
                """,
                [days],
            )

        return count
