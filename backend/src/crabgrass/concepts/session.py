"""Session concept - agent conversation tracking.

A Session tracks a conversation between a user and an AI agent.
Sessions may be associated with an Idea or be standalone.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4

from crabgrass.database import execute, fetchone, fetchall
from crabgrass.syncs.signals import session_started, session_message_added, session_ended


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────

SessionStatus = Literal["Active", "Archived"]


@dataclass
class Message:
    """A single message in a session."""

    role: Literal["user", "assistant"]
    content: str
    timestamp: str  # ISO format string


@dataclass
class Session:
    """An agent conversation session."""

    id: str
    user_id: str
    idea_id: str | None
    status: SessionStatus
    messages: list[Message] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _messages_to_json(messages: list[Message]) -> str:
    """Serialize messages to JSON for storage."""
    return json.dumps(
        [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in messages]
    )


def _messages_from_json(json_str: str | None) -> list[Message]:
    """Deserialize messages from JSON storage."""
    if not json_str:
        return []
    data = json.loads(json_str)
    return [Message(role=m["role"], content=m["content"], timestamp=m["timestamp"]) for m in data]


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────


class SessionActions:
    """Actions for the Session concept."""

    @staticmethod
    def start(user_id: str, idea_id: str | None = None) -> Session:
        """Start a new session.

        Emits: session.started
        """
        session_id = str(uuid4())
        now = datetime.utcnow()

        execute(
            """
            INSERT INTO sessions (id, user_id, idea_id, status, messages, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [session_id, user_id, idea_id, "Active", "[]", now, now],
        )

        session = Session(
            id=session_id,
            user_id=user_id,
            idea_id=idea_id,
            status="Active",
            messages=[],
            created_at=now,
            updated_at=now,
        )

        # Emit signal
        session_started.send(
            None,
            session_id=session_id,
            user_id=user_id,
            idea_id=idea_id,
        )

        return session

    @staticmethod
    def get_by_id(session_id: str) -> Session | None:
        """Get a session by ID."""
        row = fetchone(
            """
            SELECT id, user_id, idea_id, status, messages, created_at, updated_at
            FROM sessions WHERE id = ?
            """,
            [session_id],
        )
        if row:
            return Session(
                id=row[0],
                user_id=row[1],
                idea_id=row[2],
                status=row[3],
                messages=_messages_from_json(row[4]),
                created_at=row[5],
                updated_at=row[6],
            )
        return None

    @staticmethod
    def list_by_user(user_id: str, status: SessionStatus | None = None) -> list[Session]:
        """List sessions for a user."""
        query = """
            SELECT id, user_id, idea_id, status, messages, created_at, updated_at
            FROM sessions WHERE user_id = ?
        """
        params = [user_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY updated_at DESC"

        rows = fetchall(query, params)
        return [
            Session(
                id=row[0],
                user_id=row[1],
                idea_id=row[2],
                status=row[3],
                messages=_messages_from_json(row[4]),
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]

    @staticmethod
    def list_by_idea(idea_id: str) -> list[Session]:
        """List sessions for an idea."""
        rows = fetchall(
            """
            SELECT id, user_id, idea_id, status, messages, created_at, updated_at
            FROM sessions WHERE idea_id = ?
            ORDER BY updated_at DESC
            """,
            [idea_id],
        )
        return [
            Session(
                id=row[0],
                user_id=row[1],
                idea_id=row[2],
                status=row[3],
                messages=_messages_from_json(row[4]),
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]

    @staticmethod
    def add_message(
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
    ) -> Session | None:
        """Add a message to a session.

        Emits: session.message_added
        """
        session = SessionActions.get_by_id(session_id)
        if not session:
            return None

        if session.status != "Active":
            return None  # Can't add messages to archived sessions

        now = datetime.utcnow()
        new_message = Message(
            role=role,
            content=content,
            timestamp=now.isoformat(),
        )
        session.messages.append(new_message)

        execute(
            """
            UPDATE sessions
            SET messages = ?, updated_at = ?
            WHERE id = ?
            """,
            [_messages_to_json(session.messages), now, session_id],
        )

        session.updated_at = now

        # Emit signal
        session_message_added.send(
            None,
            session_id=session_id,
            user_id=session.user_id,
            idea_id=session.idea_id,
            role=role,
            content=content,
        )

        return session

    @staticmethod
    def end(session_id: str) -> Session | None:
        """End/archive a session.

        Emits: session.ended
        """
        session = SessionActions.get_by_id(session_id)
        if not session:
            return None

        now = datetime.utcnow()

        execute(
            """
            UPDATE sessions
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            ["Archived", now, session_id],
        )

        session.status = "Archived"
        session.updated_at = now

        # Emit signal
        session_ended.send(
            None,
            session_id=session_id,
            user_id=session.user_id,
            idea_id=session.idea_id,
        )

        return session

    @staticmethod
    def delete(session_id: str) -> bool:
        """Delete a session."""
        session = SessionActions.get_by_id(session_id)
        if not session:
            return False

        execute("DELETE FROM sessions WHERE id = ?", [session_id])
        return True
