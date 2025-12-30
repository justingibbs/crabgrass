"""API routes for Notifications."""

from fastapi import APIRouter, HTTPException

from crabgrass.concepts.notification import NotificationActions
from crabgrass.concepts.user import UserActions
from crabgrass.api.schemas import (
    NotificationResponse,
    NotificationCountResponse,
)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Notification endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("")
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
) -> list[NotificationResponse]:
    """List notifications for the current user."""
    current_user = UserActions.get_current()

    notifications = NotificationActions.list_for_user(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=min(max(1, limit), 100),
    )

    return [
        NotificationResponse(
            id=n.id,
            type=n.type.value,
            message=n.message,
            source_type=n.source_type,
            source_id=n.source_id,
            related_id=n.related_id,
            read=n.read,
            created_at=n.created_at,
        )
        for n in notifications
    ]


@router.get("/count")
async def get_notification_count() -> NotificationCountResponse:
    """Get count of unread notifications for the current user."""
    current_user = UserActions.get_current()
    count = NotificationActions.count_unread(current_user.id)

    return NotificationCountResponse(unread_count=count)


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: str) -> NotificationResponse:
    """Mark a notification as read."""
    notification = NotificationActions.get_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Verify ownership
    current_user = UserActions.get_current()
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")

    notification = NotificationActions.mark_read(notification_id)

    return NotificationResponse(
        id=notification.id,
        type=notification.type.value,
        message=notification.message,
        source_type=notification.source_type,
        source_id=notification.source_id,
        related_id=notification.related_id,
        read=notification.read,
        created_at=notification.created_at,
    )


@router.post("/read-all")
async def mark_all_notifications_read() -> dict:
    """Mark all notifications as read for the current user."""
    current_user = UserActions.get_current()
    count = NotificationActions.mark_all_read(current_user.id)

    return {"marked_read": count}


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(notification_id: str):
    """Delete a notification."""
    notification = NotificationActions.get_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Verify ownership
    current_user = UserActions.get_current()
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")

    NotificationActions.delete(notification_id)
