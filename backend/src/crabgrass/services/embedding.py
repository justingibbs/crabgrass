"""Embedding service - generate embeddings via Google Gemini.

Uses the google-genai SDK to generate text embeddings for semantic search.
"""

import logging
from functools import lru_cache

from google import genai
from google.genai import types

from crabgrass.config import get_settings

logger = logging.getLogger(__name__)

# Embedding dimension for text-embedding-004
EMBEDDING_DIM = 768


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        """Initialize the embedding service with API key from settings."""
        settings = get_settings()
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = "text-embedding-004"

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            List of floats representing the embedding vector (768 dimensions).
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding, returning zero vector")
            return [0.0] * EMBEDDING_DIM

        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",
                ),
            )
            return list(result.embeddings[0].values)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        results = []
        for text in texts:
            results.append(self.embed(text))
        return results


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Get singleton EmbeddingService instance."""
    return EmbeddingService()
