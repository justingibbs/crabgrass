"""IdeaObjective concept - links between Ideas and Objectives.

Tracks which Ideas address which Objectives, enabling
strategic alignment visibility.
"""

from dataclasses import dataclass
from datetime import datetime

from crabgrass.database import execute, fetchone, fetchall
from crabgrass.syncs.signals import (
    idea_linked_to_objective,
    idea_unlinked_from_objective,
)


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class IdeaObjective:
    """A link between an Idea and an Objective."""

    idea_id: str
    objective_id: str
    linked_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class IdeaObjectiveActions:
    """Actions for the IdeaObjective concept."""

    @staticmethod
    def link(idea_id: str, objective_id: str) -> IdeaObjective:
        """Link an idea to an objective.

        Emits: idea.linked_to_objective
        """
        now = datetime.utcnow()

        # Use INSERT OR IGNORE to handle duplicates gracefully
        execute(
            """
            INSERT OR IGNORE INTO idea_objectives (idea_id, objective_id, linked_at)
            VALUES (?, ?, ?)
            """,
            [idea_id, objective_id, now],
        )

        link = IdeaObjective(
            idea_id=idea_id,
            objective_id=objective_id,
            linked_at=now,
        )

        # Emit signal
        idea_linked_to_objective.send(
            None,
            idea_id=idea_id,
            objective_id=objective_id,
        )

        return link

    @staticmethod
    def unlink(idea_id: str, objective_id: str) -> bool:
        """Remove a link between an idea and an objective.

        Emits: idea.unlinked_from_objective
        """
        # Check if link exists
        existing = IdeaObjectiveActions.get(idea_id, objective_id)
        if not existing:
            return False

        execute(
            """
            DELETE FROM idea_objectives
            WHERE idea_id = ? AND objective_id = ?
            """,
            [idea_id, objective_id],
        )

        # Emit signal
        idea_unlinked_from_objective.send(
            None,
            idea_id=idea_id,
            objective_id=objective_id,
        )

        return True

    @staticmethod
    def get(idea_id: str, objective_id: str) -> IdeaObjective | None:
        """Get a specific link."""
        row = fetchone(
            """
            SELECT idea_id, objective_id, linked_at
            FROM idea_objectives
            WHERE idea_id = ? AND objective_id = ?
            """,
            [idea_id, objective_id],
        )
        if row:
            return IdeaObjective(
                idea_id=row[0],
                objective_id=row[1],
                linked_at=row[2],
            )
        return None

    @staticmethod
    def exists(idea_id: str, objective_id: str) -> bool:
        """Check if a link exists."""
        return IdeaObjectiveActions.get(idea_id, objective_id) is not None

    @staticmethod
    def list_by_idea(idea_id: str) -> list[IdeaObjective]:
        """Get all objectives linked to an idea."""
        rows = fetchall(
            """
            SELECT idea_id, objective_id, linked_at
            FROM idea_objectives
            WHERE idea_id = ?
            ORDER BY linked_at DESC
            """,
            [idea_id],
        )
        return [
            IdeaObjective(
                idea_id=row[0],
                objective_id=row[1],
                linked_at=row[2],
            )
            for row in rows
        ]

    @staticmethod
    def list_by_objective(objective_id: str) -> list[IdeaObjective]:
        """Get all ideas linked to an objective."""
        rows = fetchall(
            """
            SELECT idea_id, objective_id, linked_at
            FROM idea_objectives
            WHERE objective_id = ?
            ORDER BY linked_at DESC
            """,
            [objective_id],
        )
        return [
            IdeaObjective(
                idea_id=row[0],
                objective_id=row[1],
                linked_at=row[2],
            )
            for row in rows
        ]

    @staticmethod
    def get_idea_ids_for_objective(objective_id: str) -> list[str]:
        """Get list of idea IDs linked to an objective."""
        rows = fetchall(
            """
            SELECT idea_id
            FROM idea_objectives
            WHERE objective_id = ?
            """,
            [objective_id],
        )
        return [row[0] for row in rows]

    @staticmethod
    def get_objective_ids_for_idea(idea_id: str) -> list[str]:
        """Get list of objective IDs linked to an idea."""
        rows = fetchall(
            """
            SELECT objective_id
            FROM idea_objectives
            WHERE idea_id = ?
            """,
            [idea_id],
        )
        return [row[0] for row in rows]

    @staticmethod
    def count_ideas_for_objective(objective_id: str) -> int:
        """Count ideas linked to an objective."""
        row = fetchone(
            """
            SELECT COUNT(*)
            FROM idea_objectives
            WHERE objective_id = ?
            """,
            [objective_id],
        )
        return row[0] if row else 0

    @staticmethod
    def unlink_all_for_idea(idea_id: str) -> int:
        """Remove all objective links for an idea.

        Returns count of removed links.
        """
        rows = fetchall(
            """
            SELECT objective_id FROM idea_objectives
            WHERE idea_id = ?
            """,
            [idea_id],
        )
        count = len(rows)

        if count > 0:
            execute(
                """
                DELETE FROM idea_objectives
                WHERE idea_id = ?
                """,
                [idea_id],
            )

            # Emit signals for each unlink
            for row in rows:
                idea_unlinked_from_objective.send(
                    None,
                    idea_id=idea_id,
                    objective_id=row[0],
                )

        return count

    @staticmethod
    def unlink_all_for_objective(objective_id: str) -> int:
        """Remove all idea links for an objective.

        Returns count of removed links. Used when retiring objectives.
        """
        rows = fetchall(
            """
            SELECT idea_id FROM idea_objectives
            WHERE objective_id = ?
            """,
            [objective_id],
        )
        count = len(rows)

        if count > 0:
            execute(
                """
                DELETE FROM idea_objectives
                WHERE objective_id = ?
                """,
                [objective_id],
            )

            # Emit signals for each unlink
            for row in rows:
                idea_unlinked_from_objective.send(
                    None,
                    idea_id=row[0],
                    objective_id=objective_id,
                )

        return count
