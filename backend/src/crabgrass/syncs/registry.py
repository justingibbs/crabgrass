"""Synchronization registry - THE single source of truth.

This registry drives all signal-to-handler wiring. It's not documentation,
it's the actual configuration. To add a new sync, add one line here.

Each key is a signal name (e.g., "summary.created").
Each value is a list of handler names that fire when that signal is emitted.

V2 CHANGES:
- Embedding generation remains synchronous (fast, needed immediately)
- Similarity/relationship discovery moved to async queues
- New queue-based handlers for background agent processing
"""

SYNCHRONIZATIONS: dict[str, list[str]] = {
    # ─────────────────────────────────────────────────────────────────────────
    # Summary Changes
    # ─────────────────────────────────────────────────────────────────────────
    "summary.created": [
        "generate_summary_embedding",  # Sync: generate embedding immediately
        "enqueue_nurture",  # Async: analyze for hints, find similar
    ],
    "summary.updated": [
        "generate_summary_embedding",  # Sync: regenerate embedding
        "enqueue_connection",  # Async: find relationships
        "enqueue_nurture",  # Async: re-analyze for hints
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Challenge Changes
    # ─────────────────────────────────────────────────────────────────────────
    "challenge.created": [
        "generate_challenge_embedding",  # Sync: generate embedding
        "enqueue_connection",  # Async: find similar challenges
    ],
    "challenge.updated": [
        "generate_challenge_embedding",  # Sync: regenerate embedding
        "enqueue_connection",  # Async: find similar challenges
        "enqueue_surfacing_shared_update",  # Async: notify shared ideas
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Approach Changes
    # ─────────────────────────────────────────────────────────────────────────
    "approach.created": [
        "generate_approach_embedding",  # Sync: generate embedding
        "enqueue_connection",  # Async: find similar approaches
    ],
    "approach.updated": [
        "generate_approach_embedding",  # Sync: regenerate embedding
        "enqueue_connection",  # Async: find similar approaches
        "enqueue_surfacing_shared_update",  # Async: notify shared ideas
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Idea Lifecycle
    # ─────────────────────────────────────────────────────────────────────────
    "idea.created": [
        "enqueue_connection",  # Async: find similar ideas
        "enqueue_nurture_if_summary_only",  # Async: nurture if nascent
    ],
    "idea.updated": [
        "enqueue_connection",  # Async: update relationships
    ],
    "idea.archived": [
        "enqueue_surfacing_archived",  # Async: notify contributors
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Idea Linking (V2)
    # ─────────────────────────────────────────────────────────────────────────
    "idea.linked_to_objective": [
        "enqueue_surfacing_linked",  # Async: notify objective watchers
        "remove_from_nurture_queue",  # Remove: idea is evolving
    ],
    "idea.structure_added": [
        "remove_from_nurture_queue",  # Remove: no longer nascent
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Objective Lifecycle (V2)
    # ─────────────────────────────────────────────────────────────────────────
    "objective.created": [
        "generate_objective_embedding",  # Sync: generate embedding for similarity
        "update_objective_hierarchy",  # Sync: update graph hierarchy edges
        "enqueue_surfacing_objective_created",  # Async: notify parent watchers
    ],
    "objective.updated": [
        "generate_objective_embedding",  # Sync: regenerate embedding if description changed
        "update_objective_hierarchy",  # Sync: update graph hierarchy if parent changed
        "enqueue_surfacing_objective_updated",  # Async: notify watchers
    ],
    "objective.retired": [
        "enqueue_objective_review",  # Async: review linked ideas
        "enqueue_surfacing_objective_retired",  # Async: notify watchers
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

    # ─────────────────────────────────────────────────────────────────────────
    # Agent Processing Results (V2)
    # ─────────────────────────────────────────────────────────────────────────
    "agent.found_similarity": [
        "create_similarity_relationship",  # Sync: create graph relationship
        "record_similarity_edge",  # Sync: record to graph edge tables
        "enqueue_surfacing_similarity",  # Async: notify users
    ],
    "agent.found_relevant_user": [
        "create_interest_relationship",  # Sync: create graph edge
        "enqueue_surfacing_interest",  # Async: notify user
    ],
    "agent.suggest_reconnection": [
        "enqueue_surfacing_reconnection",  # Async: notify for review
    ],
    "agent.flag_orphan": [
        "enqueue_surfacing_orphan",  # Async: alert contributors
    ],
}
