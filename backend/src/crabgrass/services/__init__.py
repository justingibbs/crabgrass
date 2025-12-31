"""Services package - shared utilities for concepts and handlers.

Services encapsulate external integrations (like embedding APIs) and
complex queries (like similarity search).
"""

from crabgrass.services.embedding import (
    EmbeddingService,
    get_embedding_service,
    EMBEDDING_DIM,
)
from crabgrass.services.similarity import (
    SimilarityService,
    SimilarIdea,
)

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "EMBEDDING_DIM",
    "SimilarityService",
    "SimilarIdea",
]
