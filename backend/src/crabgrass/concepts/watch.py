"""Watch concept - users watching objectives or ideas.

Watches track which users want to be notified about changes
to specific objectives or ideas.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from crabgrass.database import execute, fetchone, fetchall


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────

WatchTargetType = Literal["objective", "idea"]


@dataclass
class Watch:
    """A user watching a target entity."""

    user_id: str
    target_type: WatchTargetType
    target_id: str
    created_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class WatchActions:
    """Actions for the Watch concept."""

    @staticmethod
    def create(
        user_id: str,
        target_type: WatchTargetType,
        target_id: str,
    ) -> Watch:
        """Create a new watch.

        Uses INSERT OR IGNORE to handle duplicate watches gracefully.
        """
        now = datetime.utcnow()

        # Use INSERT OR IGNORE since (user_id, target_type, target_id) is primary key
        execute(
            """
            INSERT OR IGNORE INTO watches (user_id, target_type, target_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [user_id, target_type, target_id, now],
        )

        # Return the watch (may be existing or new)
        return Watch(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            created_at=now,
        )

    @staticmethod
    def get(
        user_id: str,
        target_type: WatchTargetType,
        target_id: str,
    ) -> Watch | None:
        """Get a specific watch."""
        row = fetchone(
            """
            SELECT user_id, target_type, target_id, created_at
            FROM watches
            WHERE user_id = ? AND target_type = ? AND target_id = ?
            """,
            [user_id, target_type, target_id],
        )
        if row:
            return Watch(
                user_id=row[0],
                target_type=row[1],
                target_id=row[2],
                created_at=row[3],
            )
        return None

    @staticmethod
    def exists(
        user_id: str,
        target_type: WatchTargetType,
        target_id: str,
    ) -> bool:
        """Check if a watch exists."""
        return WatchActions.get(user_id, target_type, target_id) is not None

    @staticmethod
    def list_by_user(
        user_id: str,
        target_type: WatchTargetType | None = None,
    ) -> list[Watch]:
        """List all watches for a user."""
        if target_type:
            rows = fetchall(
                """
                SELECT user_id, target_type, target_id, created_at
                FROM watches
                WHERE user_id = ? AND target_type = ?
                ORDER BY created_at DESC
                """,
                [user_id, target_type],
            )
        else:
            rows = fetchall(
                """
                SELECT user_id, target_type, target_id, created_at
                FROM watches
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                [user_id],
            )

        return [
            Watch(
                user_id=row[0],
                target_type=row[1],
                target_id=row[2],
                created_at=row[3],
            )
            for row in rows
        ]

    @staticmethod
    def list_watchers(
        target_type: WatchTargetType,
        target_id: str,
    ) -> list[str]:
        """Get list of user IDs watching a target."""
        rows = fetchall(
            """
            SELECT user_id
            FROM watches
            WHERE target_type = ? AND target_id = ?
            """,
            [target_type, target_id],
        )
        return [row[0] for row in rows]

    @staticmethod
    def get_objective_watchers(objective_id: str) -> list[str]:
        """Get list of user IDs watching an objective.

        Convenience method for common use case.
        """
        return WatchActions.list_watchers("objective", objective_id)

    @staticmethod
    def get_idea_watchers(idea_id: str) -> list[str]:
        """Get list of user IDs watching an idea.

        Convenience method for common use case.
        """
        return WatchActions.list_watchers("idea", idea_id)

    @staticmethod
    def delete(
        user_id: str,
        target_type: WatchTargetType,
        target_id: str,
    ) -> bool:
        """Remove a watch."""
        watch = WatchActions.get(user_id, target_type, target_id)
        if not watch:
            return False

        execute(
            """
            DELETE FROM watches
            WHERE user_id = ? AND target_type = ? AND target_id = ?
            """,
            [user_id, target_type, target_id],
        )

        return True

    @staticmethod
    def delete_all_for_target(
        target_type: WatchTargetType,
        target_id: str,
    ) -> int:
        """Remove all watches for a target.

        Returns count of deleted watches.
        """
        rows = fetchall(
            """
            SELECT user_id FROM watches
            WHERE target_type = ? AND target_id = ?
            """,
            [target_type, target_id],
        )
        count = len(rows)

        if count > 0:
            execute(
                """
                DELETE FROM watches
                WHERE target_type = ? AND target_id = ?
                """,
                [target_type, target_id],
            )

        return count
