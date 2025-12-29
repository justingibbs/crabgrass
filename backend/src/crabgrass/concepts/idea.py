"""Idea concept - container for strategic responses.

An Idea groups Summary, Challenge, Approach, and CoherentActions
into a coherent unit that can be linked to Objectives.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import uuid4

from crabgrass.database import execute, fetchone, fetchall
from crabgrass.syncs.signals import idea_created, idea_updated, idea_archived


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────

Status = Literal["Draft", "Active", "Archived"]


@dataclass
class Idea:
    """A strategic response container."""

    id: str
    title: str
    status: Status
    author_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class IdeaActions:
    """Actions for the Idea concept."""

    @staticmethod
    def create(title: str, author_id: str) -> Idea:
        """Create a new Idea.

        Emits: idea.created
        """
        idea_id = str(uuid4())
        now = datetime.utcnow()

        execute(
            """
            INSERT INTO ideas (id, title, status, author_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [idea_id, title, "Draft", author_id, now, now],
        )

        idea = Idea(
            id=idea_id,
            title=title,
            status="Draft",
            author_id=author_id,
            created_at=now,
            updated_at=now,
        )

        # Emit signal
        idea_created.send(
            None,
            idea_id=idea_id,
            title=title,
            author_id=author_id,
        )

        return idea

    @staticmethod
    def get_by_id(idea_id: str) -> Idea | None:
        """Get an idea by ID."""
        row = fetchone(
            """
            SELECT id, title, status, author_id, created_at, updated_at
            FROM ideas WHERE id = ?
            """,
            [idea_id],
        )
        if row:
            return Idea(
                id=row[0],
                title=row[1],
                status=row[2],
                author_id=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    @staticmethod
    def list_all(
        author_id: str | None = None,
        status: Status | None = None,
    ) -> list[Idea]:
        """List ideas with optional filters."""
        query = """
            SELECT id, title, status, author_id, created_at, updated_at
            FROM ideas WHERE 1=1
        """
        params = []

        if author_id:
            query += " AND author_id = ?"
            params.append(author_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY updated_at DESC"

        rows = fetchall(query, params) if params else fetchall(query)
        return [
            Idea(
                id=row[0],
                title=row[1],
                status=row[2],
                author_id=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
            for row in rows
        ]

    @staticmethod
    def update(
        idea_id: str,
        title: str | None = None,
        status: Status | None = None,
    ) -> Idea | None:
        """Update an existing Idea.

        Emits: idea.updated
        """
        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            return None

        now = datetime.utcnow()
        updates = ["updated_at = ?"]
        params = [now]

        if title is not None:
            updates.append("title = ?")
            params.append(title)
            idea.title = title

        if status is not None:
            updates.append("status = ?")
            params.append(status)
            idea.status = status

        params.append(idea_id)

        execute(
            f"UPDATE ideas SET {', '.join(updates)} WHERE id = ?",
            params,
        )

        idea.updated_at = now

        # Emit signal
        idea_updated.send(
            None,
            idea_id=idea_id,
            title=title,
            status=status,
        )

        return idea

    @staticmethod
    def archive(idea_id: str) -> Idea | None:
        """Archive an idea.

        Emits: idea.archived
        """
        idea = IdeaActions.update(idea_id, status="Archived")
        if idea:
            idea_archived.send(None, idea_id=idea_id)
        return idea

    @staticmethod
    def delete(idea_id: str) -> bool:
        """Delete an idea and all related data.

        Note: In a production system, we'd use soft deletes.
        """
        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            return False

        # Delete related data first (no CASCADE in DuckDB)
        execute("DELETE FROM coherent_actions WHERE idea_id = ?", [idea_id])
        execute("DELETE FROM approaches WHERE idea_id = ?", [idea_id])
        execute("DELETE FROM challenges WHERE idea_id = ?", [idea_id])
        execute("DELETE FROM summaries WHERE idea_id = ?", [idea_id])
        execute("DELETE FROM sessions WHERE idea_id = ?", [idea_id])

        # Delete the idea
        execute("DELETE FROM ideas WHERE id = ?", [idea_id])

        return True
