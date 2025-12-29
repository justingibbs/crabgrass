"""Logging handlers - track session lifecycle events.

These handlers are plain functions with NO decorators. They're wired
to signals via the registry at startup.
"""

import logging

logger = logging.getLogger(__name__)


def log_session_start(sender, session_id: str, user_id: str, idea_id: str | None = None, **kwargs) -> None:
    """Log when a session starts.

    Called when: session.started
    """
    if idea_id:
        logger.info(f"Session {session_id} started by user {user_id} for idea {idea_id}")
    else:
        logger.info(f"Session {session_id} started by user {user_id} (no idea)")


def log_session_end(sender, session_id: str, user_id: str, idea_id: str | None = None, **kwargs) -> None:
    """Log when a session ends.

    Called when: session.ended
    """
    if idea_id:
        logger.info(f"Session {session_id} ended by user {user_id} for idea {idea_id}")
    else:
        logger.info(f"Session {session_id} ended by user {user_id}")
