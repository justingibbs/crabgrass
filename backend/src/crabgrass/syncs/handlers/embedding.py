"""Embedding handlers - generate embeddings when content changes.

These handlers are plain functions with NO decorators. They're wired
to signals via the registry at startup.
"""

import logging

logger = logging.getLogger(__name__)


def generate_summary_embedding(sender, summary_id: str, content: str, **kwargs) -> None:
    """Generate and store embedding for a Summary.

    Called when: summary.created, summary.updated
    """
    try:
        from crabgrass.services.embedding import EmbeddingService
        from crabgrass.concepts.summary import SummaryActions

        embedding = EmbeddingService().embed(content)
        SummaryActions.update_embedding(summary_id, embedding)
        logger.info(f"Generated embedding for summary {summary_id}")
    except ImportError:
        # Services not yet implemented - log and skip
        logger.warning(f"EmbeddingService not available, skipping embedding for summary {summary_id}")
    except Exception as e:
        logger.error(f"Error generating embedding for summary {summary_id}: {e}")


def generate_challenge_embedding(sender, challenge_id: str, content: str, **kwargs) -> None:
    """Generate and store embedding for a Challenge.

    Called when: challenge.created, challenge.updated
    """
    try:
        from crabgrass.services.embedding import EmbeddingService
        from crabgrass.concepts.challenge import ChallengeActions

        embedding = EmbeddingService().embed(content)
        ChallengeActions.update_embedding(challenge_id, embedding)
        logger.info(f"Generated embedding for challenge {challenge_id}")
    except ImportError:
        logger.warning(f"EmbeddingService not available, skipping embedding for challenge {challenge_id}")
    except Exception as e:
        logger.error(f"Error generating embedding for challenge {challenge_id}: {e}")


def generate_approach_embedding(sender, approach_id: str, content: str, **kwargs) -> None:
    """Generate and store embedding for an Approach.

    Called when: approach.created, approach.updated
    """
    try:
        from crabgrass.services.embedding import EmbeddingService
        from crabgrass.concepts.approach import ApproachActions

        embedding = EmbeddingService().embed(content)
        ApproachActions.update_embedding(approach_id, embedding)
        logger.info(f"Generated embedding for approach {approach_id}")
    except ImportError:
        logger.warning(f"EmbeddingService not available, skipping embedding for approach {approach_id}")
    except Exception as e:
        logger.error(f"Error generating embedding for approach {approach_id}: {e}")


def generate_objective_embedding(sender, objective_id: str, description: str = None, changes: dict = None, **kwargs) -> None:
    """Generate and store embedding for an Objective.

    Called when: objective.created (with description), objective.updated (with changes)
    For updates, only regenerates if description changed.
    """
    try:
        from crabgrass.services.embedding import EmbeddingService
        from crabgrass.concepts.objective import ObjectiveActions

        # For updates, check if description changed
        if changes is not None:
            if "description" not in changes:
                logger.debug(f"Objective {objective_id} updated but description unchanged, skipping embedding")
                return
            description = changes["description"]

        # For creates, description is passed directly
        if not description:
            # Fallback: load from database
            objective = ObjectiveActions.get_by_id(objective_id)
            if not objective:
                logger.warning(f"Objective {objective_id} not found")
                return
            description = objective.description

        embedding = EmbeddingService().embed(description)
        ObjectiveActions.update_embedding(objective_id, embedding)
        logger.info(f"Generated embedding for objective {objective_id}")
    except ImportError:
        logger.warning(f"EmbeddingService not available, skipping embedding for objective {objective_id}")
    except Exception as e:
        logger.error(f"Error generating embedding for objective {objective_id}: {e}")
