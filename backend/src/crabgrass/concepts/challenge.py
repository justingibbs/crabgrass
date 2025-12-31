"""Challenge concept - problem framing for an idea.

A Challenge articulates the problem or situation being addressed.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from crabgrass.database import execute, fetchone
from crabgrass.syncs.signals import challenge_created, challenge_updated, challenge_deleted


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Challenge:
    """A framing of the problem or situation."""

    id: str
    idea_id: str
    content: str
    embedding: list[float] | None = None  # Populated by sync handler
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class ChallengeActions:
    """Actions for the Challenge concept."""

    @staticmethod
    def create(idea_id: str, content: str) -> Challenge:
        """Create a Challenge for an Idea.

        Emits: challenge.created
        Triggers (per registry): generate_challenge_embedding
        """
        challenge_id = str(uuid4())
        now = datetime.utcnow()

        execute(
            """
            INSERT INTO challenges (id, idea_id, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [challenge_id, idea_id, content, now, now],
        )

        challenge = Challenge(
            id=challenge_id,
            idea_id=idea_id,
            content=content,
            created_at=now,
            updated_at=now,
        )

        # Emit signal
        challenge_created.send(
            None,
            challenge_id=challenge_id,
            idea_id=idea_id,
            content=content,
        )

        return challenge

    @staticmethod
    def get_by_idea_id(idea_id: str) -> Challenge | None:
        """Get the challenge for an idea."""
        row = fetchone(
            """
            SELECT id, idea_id, content, embedding, created_at, updated_at
            FROM challenges WHERE idea_id = ?
            """,
            [idea_id],
        )
        if row:
            return Challenge(
                id=row[0],
                idea_id=row[1],
                content=row[2],
                embedding=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    @staticmethod
    def get_by_id(challenge_id: str) -> Challenge | None:
        """Get a challenge by ID."""
        row = fetchone(
            """
            SELECT id, idea_id, content, embedding, created_at, updated_at
            FROM challenges WHERE id = ?
            """,
            [challenge_id],
        )
        if row:
            return Challenge(
                id=row[0],
                idea_id=row[1],
                content=row[2],
                embedding=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    @staticmethod
    def update(challenge_id: str, content: str) -> Challenge | None:
        """Update a Challenge's content.

        Emits: challenge.updated
        Triggers (per registry): generate_challenge_embedding
        """
        challenge = ChallengeActions.get_by_id(challenge_id)
        if not challenge:
            return None

        now = datetime.utcnow()

        execute(
            """
            UPDATE challenges
            SET content = ?, updated_at = ?
            WHERE id = ?
            """,
            [content, now, challenge_id],
        )

        challenge.content = content
        challenge.updated_at = now

        # Emit signal
        challenge_updated.send(
            None,
            challenge_id=challenge_id,
            idea_id=challenge.idea_id,
            content=content,
        )

        return challenge

    @staticmethod
    def delete(challenge_id: str) -> bool:
        """Delete a challenge."""
        challenge = ChallengeActions.get_by_id(challenge_id)
        if not challenge:
            return False

        execute("DELETE FROM challenges WHERE id = ?", [challenge_id])

        # Emit signal
        challenge_deleted.send(
            None,
            challenge_id=challenge_id,
            idea_id=challenge.idea_id,
        )

        return True

    @staticmethod
    def update_embedding(challenge_id: str, embedding: list[float]) -> None:
        """Update the embedding for a challenge.

        Called by the embedding sync handler, not directly by users.
        """
        execute(
            "UPDATE challenges SET embedding = ? WHERE id = ?",
            [embedding, challenge_id],
        )
