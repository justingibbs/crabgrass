"""Handler registry - maps handler names to functions.

The registry uses string names for handlers. This module provides the
mapping from those names to actual functions.
"""

from crabgrass.syncs.handlers.embedding import (
    generate_summary_embedding,
    generate_challenge_embedding,
    generate_approach_embedding,
    generate_objective_embedding,
)
from crabgrass.syncs.handlers.similarity import find_similar_ideas
from crabgrass.syncs.handlers.logging import log_session_start, log_session_end
from crabgrass.syncs.handlers.enqueue import (
    # Connection queue
    enqueue_connection,
    # Nurture queue
    enqueue_nurture,
    enqueue_nurture_if_summary_only,
    remove_from_nurture_queue,
    # Surfacing queue
    enqueue_surfacing_linked,
    enqueue_surfacing_archived,
    enqueue_surfacing_shared_update,
    enqueue_surfacing_objective_created,
    enqueue_surfacing_objective_updated,
    enqueue_surfacing_objective_retired,
    enqueue_surfacing_similarity,
    enqueue_surfacing_interest,
    enqueue_surfacing_reconnection,
    enqueue_surfacing_orphan,
    # Objective review queue
    enqueue_objective_review,
    # Graph relationships
    create_similarity_relationship,
    create_interest_relationship,
)
from crabgrass.syncs.handlers.graph import (
    update_objective_hierarchy,
    record_similarity_edge,
)


# Handler lookup by name - maps registry strings to functions
HANDLERS: dict[str, callable] = {
    # V1 handlers
    "generate_summary_embedding": generate_summary_embedding,
    "generate_challenge_embedding": generate_challenge_embedding,
    "generate_approach_embedding": generate_approach_embedding,
    "generate_objective_embedding": generate_objective_embedding,
    "find_similar_ideas": find_similar_ideas,
    "log_session_start": log_session_start,
    "log_session_end": log_session_end,
    # V2 handlers - Connection queue
    "enqueue_connection": enqueue_connection,
    # V2 handlers - Nurture queue
    "enqueue_nurture": enqueue_nurture,
    "enqueue_nurture_if_summary_only": enqueue_nurture_if_summary_only,
    "remove_from_nurture_queue": remove_from_nurture_queue,
    # V2 handlers - Surfacing queue
    "enqueue_surfacing_linked": enqueue_surfacing_linked,
    "enqueue_surfacing_archived": enqueue_surfacing_archived,
    "enqueue_surfacing_shared_update": enqueue_surfacing_shared_update,
    "enqueue_surfacing_objective_created": enqueue_surfacing_objective_created,
    "enqueue_surfacing_objective_updated": enqueue_surfacing_objective_updated,
    "enqueue_surfacing_objective_retired": enqueue_surfacing_objective_retired,
    "enqueue_surfacing_similarity": enqueue_surfacing_similarity,
    "enqueue_surfacing_interest": enqueue_surfacing_interest,
    "enqueue_surfacing_reconnection": enqueue_surfacing_reconnection,
    "enqueue_surfacing_orphan": enqueue_surfacing_orphan,
    # V2 handlers - Objective review queue
    "enqueue_objective_review": enqueue_objective_review,
    # V2 handlers - Graph relationships
    "create_similarity_relationship": create_similarity_relationship,
    "create_interest_relationship": create_interest_relationship,
    # V2 handlers - Graph edge maintenance
    "update_objective_hierarchy": update_objective_hierarchy,
    "record_similarity_edge": record_similarity_edge,
}


def get_handler(name: str) -> callable:
    """Get handler function by name.

    Raises:
        ValueError: If handler name is not registered.
    """
    if name not in HANDLERS:
        raise ValueError(f"Unknown handler: {name}. Available: {list(HANDLERS.keys())}")
    return HANDLERS[name]


__all__ = [
    "HANDLERS",
    "get_handler",
    # V1
    "generate_summary_embedding",
    "generate_challenge_embedding",
    "generate_approach_embedding",
    "generate_objective_embedding",
    "find_similar_ideas",
    "log_session_start",
    "log_session_end",
    # V2 - Connection
    "enqueue_connection",
    # V2 - Nurture
    "enqueue_nurture",
    "enqueue_nurture_if_summary_only",
    "remove_from_nurture_queue",
    # V2 - Surfacing
    "enqueue_surfacing_linked",
    "enqueue_surfacing_archived",
    "enqueue_surfacing_shared_update",
    "enqueue_surfacing_objective_created",
    "enqueue_surfacing_objective_updated",
    "enqueue_surfacing_objective_retired",
    "enqueue_surfacing_similarity",
    "enqueue_surfacing_interest",
    "enqueue_surfacing_reconnection",
    "enqueue_surfacing_orphan",
    # V2 - Objective review
    "enqueue_objective_review",
    # V2 - Graph
    "create_similarity_relationship",
    "create_interest_relationship",
    "update_objective_hierarchy",
    "record_similarity_edge",
]
