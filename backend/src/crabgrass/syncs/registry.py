"""Synchronization registry - THE single source of truth.

This registry drives all signal-to-handler wiring. It's not documentation,
it's the actual configuration. To add a new sync, add one line here.

Each key is a signal name (e.g., "summary.created").
Each value is a list of handler names that fire when that signal is emitted.
"""

SYNCHRONIZATIONS: dict[str, list[str]] = {
    # ─────────────────────────────────────────────────────────────────────────
    # Summary Changes
    # ─────────────────────────────────────────────────────────────────────────
    "summary.created": [
        "generate_summary_embedding",
    ],
    "summary.updated": [
        "generate_summary_embedding",
        "find_similar_ideas",
    ],
    # ─────────────────────────────────────────────────────────────────────────
    # Challenge Changes
    # ─────────────────────────────────────────────────────────────────────────
    "challenge.created": [
        "generate_challenge_embedding",
    ],
    "challenge.updated": [
        "generate_challenge_embedding",
    ],
    # ─────────────────────────────────────────────────────────────────────────
    # Approach Changes
    # ─────────────────────────────────────────────────────────────────────────
    "approach.created": [
        "generate_approach_embedding",
    ],
    "approach.updated": [
        "generate_approach_embedding",
    ],
    # ─────────────────────────────────────────────────────────────────────────
    # Idea Lifecycle
    # ─────────────────────────────────────────────────────────────────────────
    "idea.created": [
        "find_similar_ideas",
    ],
    # ─────────────────────────────────────────────────────────────────────────
    # Session Management
    # ─────────────────────────────────────────────────────────────────────────
    "session.started": [
        "log_session_start",
    ],
    "session.ended": [
        "log_session_end",
    ],
}
