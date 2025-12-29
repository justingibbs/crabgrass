"""Similarity handlers - find related ideas when content changes.

These handlers are plain functions with NO decorators. They're wired
to signals via the registry at startup.
"""

import logging

logger = logging.getLogger(__name__)


def find_similar_ideas(sender, idea_id: str, **kwargs) -> list | None:
    """Find ideas similar to the given idea.

    Called when: idea.created, summary.updated

    In demo v1, the result is logged and could be returned to caller.
    In future versions, this would queue results for SurfacingAgent.
    """
    try:
        from crabgrass.services.similarity import SimilarityService

        similar = SimilarityService().find_similar_for_idea(idea_id)
        if similar:
            logger.info(f"Found {len(similar)} similar ideas for idea {idea_id}")
        return similar
    except ImportError:
        logger.warning(f"SimilarityService not available, skipping similarity search for idea {idea_id}")
        return None
    except Exception as e:
        logger.error(f"Error finding similar ideas for {idea_id}: {e}")
        return None
