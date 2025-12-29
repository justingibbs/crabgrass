"""User concept - represents people in the system.

For the demo, users are mocked with no authentication.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from crabgrass.database import execute, fetchone, fetchall


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────

Role = Literal["Frontline", "Senior"]


@dataclass
class User:
    """A person in the system."""

    id: str
    name: str
    email: str
    role: Role
    created_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Mock Users (for demo)
# ─────────────────────────────────────────────────────────────────────────────

MOCK_USERS = [
    User(
        id="user-sarah",
        name="Sarah",
        email="sarah@example.com",
        role="Frontline",
    ),
    User(
        id="user-vp-sales",
        name="VP Sales",
        email="vpsales@example.com",
        role="Senior",
    ),
    User(
        id="user-marcus",
        name="Marcus",
        email="marcus@example.com",
        role="Frontline",
    ),
    User(
        id="user-diana",
        name="Diana",
        email="diana@example.com",
        role="Frontline",
    ),
]

# Default user for the demo
DEFAULT_USER_ID = "user-sarah"

# Current user (mutable for demo role toggle)
_current_user_id: str = DEFAULT_USER_ID


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class UserActions:
    """Actions for the User concept."""

    @staticmethod
    def set_current(user_id: str) -> None:
        """Set the current user (for demo role toggle).

        In a real app, this would be handled by auth.
        """
        global _current_user_id
        _current_user_id = user_id

    @staticmethod
    def ensure_mock_users_exist() -> None:
        """Ensure mock users exist in the database.

        Called during app startup to seed demo users.
        """
        for user in MOCK_USERS:
            existing = fetchone(
                "SELECT id FROM users WHERE id = ?",
                [user.id],
            )
            if not existing:
                execute(
                    """
                    INSERT INTO users (id, name, email, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    [user.id, user.name, user.email, user.role],
                )

    @staticmethod
    def get_by_id(user_id: str) -> User | None:
        """Get a user by ID."""
        row = fetchone(
            """
            SELECT id, name, email, role, created_at
            FROM users WHERE id = ?
            """,
            [user_id],
        )
        if row:
            return User(
                id=row[0],
                name=row[1],
                email=row[2],
                role=row[3],
                created_at=row[4],
            )
        return None

    @staticmethod
    def get_current() -> User:
        """Get the current user.

        For demo purposes, returns the selected mock user.
        In a real app, this would use session/auth.
        """
        user = UserActions.get_by_id(_current_user_id)
        if not user:
            # Ensure mock users exist and try again
            UserActions.ensure_mock_users_exist()
            user = UserActions.get_by_id(_current_user_id)
        return user

    @staticmethod
    def list_all() -> list[User]:
        """List all users."""
        rows = fetchall(
            """
            SELECT id, name, email, role, created_at
            FROM users ORDER BY name
            """
        )
        return [
            User(
                id=row[0],
                name=row[1],
                email=row[2],
                role=row[3],
                created_at=row[4],
            )
            for row in rows
        ]
