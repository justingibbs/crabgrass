"""CoherentAction concept - specific implementation steps.

CoherentActions are specific steps that implement the Approach.
They form a coherent set of actions to achieve the strategy.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import uuid4

from crabgrass.database import execute, fetchone, fetchall
from crabgrass.syncs.signals import action_created, action_updated, action_completed, action_deleted


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────

ActionStatus = Literal["Pending", "In Progress", "Complete"]


@dataclass
class CoherentAction:
    """A specific step that implements the Approach."""

    id: str
    idea_id: str
    content: str
    status: ActionStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class CoherentActionActions:
    """Actions for the CoherentAction concept."""

    @staticmethod
    def create(idea_id: str, content: str) -> CoherentAction:
        """Create a CoherentAction for an Idea.

        Emits: action.created
        """
        action_id = str(uuid4())
        now = datetime.utcnow()

        execute(
            """
            INSERT INTO coherent_actions (id, idea_id, content, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [action_id, idea_id, content, "Pending", now, now],
        )

        action = CoherentAction(
            id=action_id,
            idea_id=idea_id,
            content=content,
            status="Pending",
            created_at=now,
            updated_at=now,
        )

        # Emit signal
        action_created.send(
            None,
            action_id=action_id,
            idea_id=idea_id,
            content=content,
        )

        return action

    @staticmethod
    def get_by_id(action_id: str) -> CoherentAction | None:
        """Get an action by ID."""
        row = fetchone(
            """
            SELECT id, idea_id, content, status, created_at, updated_at
            FROM coherent_actions WHERE id = ?
            """,
            [action_id],
        )
        if row:
            return CoherentAction(
                id=row[0],
                idea_id=row[1],
                content=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    @staticmethod
    def list_by_idea_id(idea_id: str) -> list[CoherentAction]:
        """Get all actions for an idea."""
        rows = fetchall(
            """
            SELECT id, idea_id, content, status, created_at, updated_at
            FROM coherent_actions WHERE idea_id = ?
            ORDER BY created_at
            """,
            [idea_id],
        )
        return [
            CoherentAction(
                id=row[0],
                idea_id=row[1],
                content=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
            for row in rows
        ]

    @staticmethod
    def update(
        action_id: str,
        content: str | None = None,
        status: ActionStatus | None = None,
    ) -> CoherentAction | None:
        """Update a CoherentAction.

        Emits: action.updated
        """
        action = CoherentActionActions.get_by_id(action_id)
        if not action:
            return None

        now = datetime.utcnow()
        updates = ["updated_at = ?"]
        params = [now]

        if content is not None:
            updates.append("content = ?")
            params.append(content)
            action.content = content

        if status is not None:
            updates.append("status = ?")
            params.append(status)
            action.status = status

        params.append(action_id)

        execute(
            f"UPDATE coherent_actions SET {', '.join(updates)} WHERE id = ?",
            params,
        )

        action.updated_at = now

        # Emit signal
        action_updated.send(
            None,
            action_id=action_id,
            idea_id=action.idea_id,
            content=content,
            status=status,
        )

        return action

    @staticmethod
    def complete(action_id: str) -> CoherentAction | None:
        """Mark an action as complete.

        Emits: action.completed
        """
        action = CoherentActionActions.update(action_id, status="Complete")
        if action:
            action_completed.send(
                None,
                action_id=action_id,
                idea_id=action.idea_id,
            )
        return action

    @staticmethod
    def delete(action_id: str) -> bool:
        """Delete an action."""
        action = CoherentActionActions.get_by_id(action_id)
        if not action:
            return False

        execute("DELETE FROM coherent_actions WHERE id = ?", [action_id])

        # Emit signal
        action_deleted.send(
            None,
            action_id=action_id,
            idea_id=action.idea_id,
        )

        return True
