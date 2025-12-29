"""Summary concept - freeform description of an idea.

The Summary is the low-barrier entry point for capturing ideas.
Users can jot down hunches without pressure to structure them.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from crabgrass.database import execute, fetchone
from crabgrass.syncs.signals import summary_created, summary_updated


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Summary:
    """A freeform description of an idea."""

    id: str
    idea_id: str
    content: str
    embedding: list[float] | None = None  # Populated by sync handler
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class SummaryActions:
    """Actions for the Summary concept."""

    @staticmethod
    def create(idea_id: str, content: str) -> Summary:
        """Create a Summary for an Idea.

        Emits: summary.created
        Triggers (per registry): generate_summary_embedding
        """
        summary_id = str(uuid4())
        now = datetime.utcnow()

        execute(
            """
            INSERT INTO summaries (id, idea_id, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [summary_id, idea_id, content, now, now],
        )

        summary = Summary(
            id=summary_id,
            idea_id=idea_id,
            content=content,
            created_at=now,
            updated_at=now,
        )

        # Emit signal - embedding handler will populate embedding field
        summary_created.send(
            None,
            summary_id=summary_id,
            idea_id=idea_id,
            content=content,
        )

        return summary

    @staticmethod
    def get_by_idea_id(idea_id: str) -> Summary | None:
        """Get the summary for an idea."""
        row = fetchone(
            """
            SELECT id, idea_id, content, embedding, created_at, updated_at
            FROM summaries WHERE idea_id = ?
            """,
            [idea_id],
        )
        if row:
            return Summary(
                id=row[0],
                idea_id=row[1],
                content=row[2],
                embedding=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    @staticmethod
    def get_by_id(summary_id: str) -> Summary | None:
        """Get a summary by ID."""
        row = fetchone(
            """
            SELECT id, idea_id, content, embedding, created_at, updated_at
            FROM summaries WHERE id = ?
            """,
            [summary_id],
        )
        if row:
            return Summary(
                id=row[0],
                idea_id=row[1],
                content=row[2],
                embedding=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    @staticmethod
    def update(summary_id: str, content: str) -> Summary | None:
        """Update a Summary's content.

        Emits: summary.updated
        Triggers (per registry): generate_summary_embedding, find_similar_ideas
        """
        summary = SummaryActions.get_by_id(summary_id)
        if not summary:
            return None

        now = datetime.utcnow()

        execute(
            """
            UPDATE summaries
            SET content = ?, updated_at = ?
            WHERE id = ?
            """,
            [content, now, summary_id],
        )

        summary.content = content
        summary.updated_at = now

        # Emit signal
        summary_updated.send(
            None,
            summary_id=summary_id,
            idea_id=summary.idea_id,
            content=content,
        )

        return summary

    @staticmethod
    def update_embedding(summary_id: str, embedding: list[float]) -> None:
        """Update the embedding for a summary.

        Called by the embedding sync handler, not directly by users.
        """
        execute(
            "UPDATE summaries SET embedding = ? WHERE id = ?",
            [embedding, summary_id],
        )
