"""Handler registry - maps handler names to functions.

The registry uses string names for handlers. This module provides the
mapping from those names to actual functions.
"""

from crabgrass.syncs.handlers.embedding import (
    generate_summary_embedding,
    generate_challenge_embedding,
    generate_approach_embedding,
)
from crabgrass.syncs.handlers.similarity import find_similar_ideas
from crabgrass.syncs.handlers.logging import log_session_start, log_session_end


# Handler lookup by name - maps registry strings to functions
HANDLERS: dict[str, callable] = {
    "generate_summary_embedding": generate_summary_embedding,
    "generate_challenge_embedding": generate_challenge_embedding,
    "generate_approach_embedding": generate_approach_embedding,
    "find_similar_ideas": find_similar_ideas,
    "log_session_start": log_session_start,
    "log_session_end": log_session_end,
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
    "generate_summary_embedding",
    "generate_challenge_embedding",
    "generate_approach_embedding",
    "find_similar_ideas",
    "log_session_start",
    "log_session_end",
]
