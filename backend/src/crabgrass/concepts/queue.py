"""Queue concept - async processing infrastructure.

Queues decouple concept changes from agent processing.
Agents subscribe to relevant queues and process items asynchronously.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from crabgrass.database import execute, fetchone, fetchall


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────


class QueueName(str, Enum):
    """Available queues for async processing."""

    CONNECTION = "connection"  # Items needing relationship analysis
    NURTURE = "nurture"  # Nascent ideas needing encouragement
    SURFACING = "surfacing"  # Items needing user notification
    OBJECTIVE_REVIEW = "objective_review"  # Ideas needing review after objective changes


class QueueItemStatus(str, Enum):
    """Status of a queue item."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class QueueItem:
    """An item in an async processing queue."""

    id: str
    queue: QueueName
    payload: dict[str, Any]
    status: QueueItemStatus
    attempts: int
    created_at: datetime | None = None
    processed_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _payload_to_json(payload: dict[str, Any]) -> str:
    """Serialize payload to JSON for storage."""
    return json.dumps(payload)


def _payload_from_json(json_str: str | None) -> dict[str, Any]:
    """Deserialize payload from JSON storage."""
    if not json_str:
        return {}
    return json.loads(json_str)


def _row_to_queue_item(row: tuple) -> QueueItem:
    """Convert a database row to a QueueItem."""
    return QueueItem(
        id=row[0],
        queue=QueueName(row[1]),
        payload=_payload_from_json(row[2]),
        status=QueueItemStatus(row[3]),
        attempts=row[4],
        created_at=row[5],
        processed_at=row[6],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class QueueActions:
    """Actions for queue management.

    Note: Queue operations don't emit signals - they are the destination
    for other signals and are processed by background agents.
    """

    @staticmethod
    def enqueue(queue: QueueName, payload: dict[str, Any]) -> QueueItem:
        """Add item to a queue.

        Args:
            queue: Which queue to add to
            payload: Event data for the handler

        Returns:
            The created queue item
        """
        item_id = str(uuid4())
        now = datetime.utcnow()

        execute(
            """
            INSERT INTO queue_items (id, queue, payload, status, attempts, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [item_id, queue.value, _payload_to_json(payload), QueueItemStatus.PENDING.value, 0, now],
        )

        return QueueItem(
            id=item_id,
            queue=queue,
            payload=payload,
            status=QueueItemStatus.PENDING,
            attempts=0,
            created_at=now,
            processed_at=None,
        )

    @staticmethod
    def dequeue(queue: QueueName, limit: int = 10) -> list[QueueItem]:
        """Get pending items from a queue and mark as processing.

        Args:
            queue: Which queue to read from
            limit: Maximum items to return

        Returns:
            List of items now marked as processing
        """
        # Get pending items ordered by creation time
        rows = fetchall(
            """
            SELECT id, queue, payload, status, attempts, created_at, processed_at
            FROM queue_items
            WHERE queue = ? AND status = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            [queue.value, QueueItemStatus.PENDING.value, limit],
        )

        items = [_row_to_queue_item(row) for row in rows]

        # Mark them as processing
        if items:
            item_ids = [item.id for item in items]
            placeholders = ", ".join(["?" for _ in item_ids])
            execute(
                f"""
                UPDATE queue_items
                SET status = ?
                WHERE id IN ({placeholders})
                """,
                [QueueItemStatus.PROCESSING.value] + item_ids,
            )

            # Update local objects
            for item in items:
                item.status = QueueItemStatus.PROCESSING

        return items

    @staticmethod
    def complete(item_id: str) -> QueueItem | None:
        """Mark item as completed.

        Args:
            item_id: ID of the item to complete

        Returns:
            Updated queue item, or None if not found
        """
        now = datetime.utcnow()

        execute(
            """
            UPDATE queue_items
            SET status = ?, processed_at = ?
            WHERE id = ?
            """,
            [QueueItemStatus.COMPLETED.value, now, item_id],
        )

        return QueueActions.get_by_id(item_id)

    @staticmethod
    def fail(item_id: str) -> QueueItem | None:
        """Mark item as failed, increment attempts.

        Args:
            item_id: ID of the item that failed

        Returns:
            Updated queue item, or None if not found
        """
        item = QueueActions.get_by_id(item_id)
        if not item:
            return None

        execute(
            """
            UPDATE queue_items
            SET status = ?, attempts = ?
            WHERE id = ?
            """,
            [QueueItemStatus.FAILED.value, item.attempts + 1, item_id],
        )

        item.status = QueueItemStatus.FAILED
        item.attempts += 1
        return item

    @staticmethod
    def retry_failed(queue: QueueName, max_attempts: int = 3) -> int:
        """Re-queue failed items that haven't exceeded max attempts.

        Args:
            queue: Which queue to check
            max_attempts: Maximum retry attempts

        Returns:
            Number of items re-queued
        """
        result = execute(
            """
            UPDATE queue_items
            SET status = ?
            WHERE queue = ? AND status = ? AND attempts < ?
            """,
            [QueueItemStatus.PENDING.value, queue.value, QueueItemStatus.FAILED.value, max_attempts],
        )

        # DuckDB execute returns the connection, we need rowcount differently
        # For now, return count via a separate query
        row = fetchone(
            """
            SELECT COUNT(*)
            FROM queue_items
            WHERE queue = ? AND status = ? AND attempts < ?
            """,
            [queue.value, QueueItemStatus.PENDING.value, max_attempts],
        )

        return row[0] if row else 0

    @staticmethod
    def get_by_id(item_id: str) -> QueueItem | None:
        """Get a queue item by ID."""
        row = fetchone(
            """
            SELECT id, queue, payload, status, attempts, created_at, processed_at
            FROM queue_items WHERE id = ?
            """,
            [item_id],
        )

        if row:
            return _row_to_queue_item(row)
        return None

    @staticmethod
    def count_pending(queue: QueueName) -> int:
        """Count pending items in a queue."""
        row = fetchone(
            """
            SELECT COUNT(*)
            FROM queue_items
            WHERE queue = ? AND status = ?
            """,
            [queue.value, QueueItemStatus.PENDING.value],
        )

        return row[0] if row else 0

    @staticmethod
    def count_by_status(queue: QueueName) -> dict[str, int]:
        """Get counts for each status in a queue."""
        rows = fetchall(
            """
            SELECT status, COUNT(*)
            FROM queue_items
            WHERE queue = ?
            GROUP BY status
            """,
            [queue.value],
        )

        return {row[0]: row[1] for row in rows}

    @staticmethod
    def cleanup_completed(older_than_hours: int = 24) -> int:
        """Delete completed items older than specified hours.

        Args:
            older_than_hours: Delete items completed more than this many hours ago

        Returns:
            Number of items deleted
        """
        execute(
            """
            DELETE FROM queue_items
            WHERE status = ?
              AND processed_at < CURRENT_TIMESTAMP - INTERVAL ? HOUR
            """,
            [QueueItemStatus.COMPLETED.value, older_than_hours],
        )

        # Return count (approximate - DuckDB doesn't give rowcount easily)
        return 0  # TODO: implement actual count

    @staticmethod
    def remove_by_payload_match(queue: QueueName, **match_fields) -> int:
        """Remove pending items matching payload fields.

        Useful for removing items that are no longer relevant
        (e.g., remove nurture items when idea gains structure).

        Args:
            queue: Queue to search
            **match_fields: Payload fields that must match

        Returns:
            Number of items removed
        """
        # Get pending items for this queue
        rows = fetchall(
            """
            SELECT id, payload
            FROM queue_items
            WHERE queue = ? AND status = ?
            """,
            [queue.value, QueueItemStatus.PENDING.value],
        )

        items_to_remove = []
        for row in rows:
            payload = _payload_from_json(row[1])
            # Check if all match_fields are present and equal
            if all(payload.get(k) == v for k, v in match_fields.items()):
                items_to_remove.append(row[0])

        if items_to_remove:
            placeholders = ", ".join(["?" for _ in items_to_remove])
            execute(
                f"DELETE FROM queue_items WHERE id IN ({placeholders})",
                items_to_remove,
            )

        return len(items_to_remove)
