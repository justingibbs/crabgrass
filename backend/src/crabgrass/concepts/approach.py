"""Approach concept - guiding policy to address a challenge.

An Approach is the overall strategy chosen to address the Challenge.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from crabgrass.database import execute, fetchone
from crabgrass.syncs.signals import approach_created, approach_updated, approach_deleted


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Approach:
    """A guiding policy to address a challenge."""

    id: str
    idea_id: str
    content: str
    embedding: list[float] | None = None  # Populated by sync handler
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class ApproachActions:
    """Actions for the Approach concept."""

    @staticmethod
    def create(idea_id: str, content: str) -> Approach:
        """Create an Approach for an Idea.

        Emits: approach.created
        Triggers (per registry): generate_approach_embedding
        """
        approach_id = str(uuid4())
        now = datetime.utcnow()

        execute(
            """
            INSERT INTO approaches (id, idea_id, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [approach_id, idea_id, content, now, now],
        )

        approach = Approach(
            id=approach_id,
            idea_id=idea_id,
            content=content,
            created_at=now,
            updated_at=now,
        )

        # Emit signal
        approach_created.send(
            None,
            approach_id=approach_id,
            idea_id=idea_id,
            content=content,
        )

        return approach

    @staticmethod
    def get_by_idea_id(idea_id: str) -> Approach | None:
        """Get the approach for an idea."""
        row = fetchone(
            """
            SELECT id, idea_id, content, embedding, created_at, updated_at
            FROM approaches WHERE idea_id = ?
            """,
            [idea_id],
        )
        if row:
            return Approach(
                id=row[0],
                idea_id=row[1],
                content=row[2],
                embedding=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    @staticmethod
    def get_by_id(approach_id: str) -> Approach | None:
        """Get an approach by ID."""
        row = fetchone(
            """
            SELECT id, idea_id, content, embedding, created_at, updated_at
            FROM approaches WHERE id = ?
            """,
            [approach_id],
        )
        if row:
            return Approach(
                id=row[0],
                idea_id=row[1],
                content=row[2],
                embedding=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    @staticmethod
    def update(approach_id: str, content: str) -> Approach | None:
        """Update an Approach's content.

        Emits: approach.updated
        Triggers (per registry): generate_approach_embedding
        """
        approach = ApproachActions.get_by_id(approach_id)
        if not approach:
            return None

        now = datetime.utcnow()

        execute(
            """
            UPDATE approaches
            SET content = ?, updated_at = ?
            WHERE id = ?
            """,
            [content, now, approach_id],
        )

        approach.content = content
        approach.updated_at = now

        # Emit signal
        approach_updated.send(
            None,
            approach_id=approach_id,
            idea_id=approach.idea_id,
            content=content,
        )

        return approach

    @staticmethod
    def delete(approach_id: str) -> bool:
        """Delete an approach."""
        approach = ApproachActions.get_by_id(approach_id)
        if not approach:
            return False

        execute("DELETE FROM approaches WHERE id = ?", [approach_id])

        # Emit signal
        approach_deleted.send(
            None,
            approach_id=approach_id,
            idea_id=approach.idea_id,
        )

        return True

    @staticmethod
    def update_embedding(approach_id: str, embedding: list[float]) -> None:
        """Update the embedding for an approach.

        Called by the embedding sync handler, not directly by users.
        """
        execute(
            "UPDATE approaches SET embedding = ? WHERE id = ?",
            [embedding, approach_id],
        )
