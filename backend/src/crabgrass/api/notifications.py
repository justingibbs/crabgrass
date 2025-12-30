"""API routes for Notifications."""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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


@router.post("/read-all")
async def mark_all_notifications_read() -> dict:
    """Mark all notifications as read for the current user."""
    current_user = UserActions.get_current()
    count = NotificationActions.mark_all_read(current_user.id)

    return {"marked_read": count}


# ─────────────────────────────────────────────────────────────────────────────
# Demo / All-Users Endpoints
# NOTE: These must come BEFORE /{notification_id} routes to avoid path conflicts
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/all")
async def list_all_notifications(
    limit: int = 50,
) -> list[NotificationResponse]:
    """List all notifications (for demo purposes).

    Shows notifications for all users, sorted by creation time.
    """
    notifications = NotificationActions.list_all(limit=min(max(1, limit), 100))

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


@router.delete("/all", status_code=204)
async def clear_all_notifications():
    """Clear all notifications (for demo reset)."""
    NotificationActions.clear_all()


# ─────────────────────────────────────────────────────────────────────────────
# SSE Stream Endpoint
# ─────────────────────────────────────────────────────────────────────────────


async def notification_event_generator():
    """Generate SSE events for notifications.

    Polls for new notifications and sends them as SSE events.
    """
    last_check = datetime.utcnow()

    while True:
        try:
            # Get notifications created since last check
            new_notifications = NotificationActions.list_since(last_check)
            last_check = datetime.utcnow()

            for notification in new_notifications:
                data = {
                    "id": notification.id,
                    "type": notification.type.value,
                    "message": notification.message,
                    "source_type": notification.source_type,
                    "source_id": notification.source_id,
                    "related_id": notification.related_id,
                    "read": notification.read,
                    "created_at": notification.created_at.isoformat() if notification.created_at else None,
                }
                yield f"data: {json.dumps(data)}\n\n"

            # Send heartbeat every 15 seconds to keep connection alive
            yield ": heartbeat\n\n"

            # Poll interval
            await asyncio.sleep(2)

        except asyncio.CancelledError:
            break
        except Exception:
            # On error, wait and retry
            await asyncio.sleep(5)


@router.get("/stream")
async def stream_notifications():
    """Stream notifications via Server-Sent Events (SSE).

    Returns a stream of new notifications as they are created.
    Connect to this endpoint with EventSource in the browser.
    """
    return StreamingResponse(
        notification_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Individual Notification Endpoints (must come AFTER static paths)
# ─────────────────────────────────────────────────────────────────────────────


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
