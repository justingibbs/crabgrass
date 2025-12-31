"""Objective concept - organizational goals that Ideas can address.

Objectives form a flexible hierarchy via parent_id relationships.
Ideas can be linked to Objectives to show strategic alignment.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import uuid4

from crabgrass.database import execute, fetchone, fetchall
from crabgrass.syncs.signals import (
    objective_created,
    objective_updated,
    objective_retired,
)


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────

ObjectiveStatus = Literal["Active", "Retired"]


@dataclass
class Objective:
    """An organizational objective or goal."""

    id: str
    title: str
    description: str
    status: ObjectiveStatus
    author_id: str
    parent_id: str | None = None
    embedding: list[float] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class ObjectiveActions:
    """Actions for the Objective concept."""

    @staticmethod
    def create(
        title: str,
        description: str,
        author_id: str,
        parent_id: str | None = None,
    ) -> Objective:
        """Create a new Objective.

        Emits: objective.created
        """
        objective_id = str(uuid4())
        now = datetime.utcnow()

        execute(
            """
            INSERT INTO objectives (id, title, description, status, author_id, parent_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [objective_id, title, description, "Active", author_id, parent_id, now, now],
        )

        objective = Objective(
            id=objective_id,
            title=title,
            description=description,
            status="Active",
            author_id=author_id,
            parent_id=parent_id,
            created_at=now,
            updated_at=now,
        )

        # Emit signal
        objective_created.send(
            None,
            objective_id=objective_id,
            title=title,
            description=description,
            author_id=author_id,
            parent_id=parent_id,
        )

        return objective

    @staticmethod
    def get_by_id(objective_id: str) -> Objective | None:
        """Get an objective by ID."""
        row = fetchone(
            """
            SELECT id, title, description, status, author_id, parent_id, embedding, created_at, updated_at
            FROM objectives WHERE id = ?
            """,
            [objective_id],
        )
        if row:
            return Objective(
                id=row[0],
                title=row[1],
                description=row[2],
                status=row[3],
                author_id=row[4],
                parent_id=row[5],
                embedding=row[6],
                created_at=row[7],
                updated_at=row[8],
            )
        return None

    @staticmethod
    def list_all(
        status: ObjectiveStatus | None = None,
        author_id: str | None = None,
        parent_id: str | None = None,
    ) -> list[Objective]:
        """List objectives with optional filters."""
        query = """
            SELECT id, title, description, status, author_id, parent_id, embedding, created_at, updated_at
            FROM objectives WHERE 1=1
        """
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if author_id:
            query += " AND author_id = ?"
            params.append(author_id)

        if parent_id is not None:
            if parent_id == "":
                # Empty string means top-level objectives (no parent)
                query += " AND parent_id IS NULL"
            else:
                query += " AND parent_id = ?"
                params.append(parent_id)

        query += " ORDER BY updated_at DESC"

        rows = fetchall(query, params) if params else fetchall(query)
        return [
            Objective(
                id=row[0],
                title=row[1],
                description=row[2],
                status=row[3],
                author_id=row[4],
                parent_id=row[5],
                embedding=row[6],
                created_at=row[7],
                updated_at=row[8],
            )
            for row in rows
        ]

    @staticmethod
    def list_active() -> list[Objective]:
        """List all active objectives."""
        return ObjectiveActions.list_all(status="Active")

    @staticmethod
    def get_sub_objectives(objective_id: str) -> list[Objective]:
        """Get child objectives that contribute to this one."""
        return ObjectiveActions.list_all(parent_id=objective_id)

    @staticmethod
    def update(
        objective_id: str,
        title: str | None = None,
        description: str | None = None,
        parent_id: str | None = None,
    ) -> Objective | None:
        """Update an existing Objective.

        Emits: objective.updated
        """
        objective = ObjectiveActions.get_by_id(objective_id)
        if not objective:
            return None

        now = datetime.utcnow()
        updates = ["updated_at = ?"]
        params: list = [now]
        changes = {}

        if title is not None:
            updates.append("title = ?")
            params.append(title)
            objective.title = title
            changes["title"] = title

        if description is not None:
            updates.append("description = ?")
            params.append(description)
            objective.description = description
            changes["description"] = description

        if parent_id is not None:
            updates.append("parent_id = ?")
            params.append(parent_id if parent_id else None)
            objective.parent_id = parent_id if parent_id else None
            changes["parent_id"] = parent_id

        params.append(objective_id)

        execute(
            f"UPDATE objectives SET {', '.join(updates)} WHERE id = ?",
            params,
        )

        objective.updated_at = now

        # Emit signal
        objective_updated.send(
            None,
            objective_id=objective_id,
            changes=changes,
        )

        return objective

    @staticmethod
    def retire(objective_id: str) -> Objective | None:
        """Retire an objective (soft delete).

        Emits: objective.retired
        """
        objective = ObjectiveActions.get_by_id(objective_id)
        if not objective:
            return None

        now = datetime.utcnow()
        execute(
            "UPDATE objectives SET status = ?, updated_at = ? WHERE id = ?",
            ["Retired", now, objective_id],
        )

        objective.status = "Retired"
        objective.updated_at = now

        # Emit signal - this triggers review of linked ideas
        objective_retired.send(
            None,
            objective_id=objective_id,
        )

        return objective

    @staticmethod
    def update_embedding(objective_id: str, embedding: list[float]) -> bool:
        """Update the embedding for an objective.

        Called by sync handlers after embedding generation.
        """
        result = execute(
            "UPDATE objectives SET embedding = ? WHERE id = ?",
            [embedding, objective_id],
        )
        return result is not None

    @staticmethod
    def delete(objective_id: str) -> bool:
        """Delete an objective.

        Note: In production, prefer retire() for soft deletes.
        This also cleans up related data.
        """
        objective = ObjectiveActions.get_by_id(objective_id)
        if not objective:
            return False

        # Delete related data first
        execute("DELETE FROM idea_objectives WHERE objective_id = ?", [objective_id])
        execute("DELETE FROM watches WHERE target_type = 'objective' AND target_id = ?", [objective_id])

        # Update child objectives to remove parent reference
        execute("UPDATE objectives SET parent_id = NULL WHERE parent_id = ?", [objective_id])

        # Delete the objective
        execute("DELETE FROM objectives WHERE id = ?", [objective_id])

        return True
