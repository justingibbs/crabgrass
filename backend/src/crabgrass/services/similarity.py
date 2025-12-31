"""Similarity service - find related ideas using vector similarity.

Uses DuckDB's vector similarity search (VSS) to find semantically similar content.
"""

import logging
from dataclasses import dataclass

from crabgrass.database import fetchall, fetchone
from crabgrass.services.embedding import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class SimilarIdea:
    """Result of a similarity search for ideas."""

    idea_id: str
    title: str
    similarity: float


@dataclass
class SimilarObjective:
    """Result of a similarity search for objectives."""

    objective_id: str
    title: str
    similarity: float


class SimilarityService:
    """Service for finding similar ideas."""

    def __init__(self, embedding_service: EmbeddingService | None = None):
        """Initialize the similarity service.

        Args:
            embedding_service: Optional embedding service. If not provided,
                uses the singleton instance.
        """
        self._embedding_service = embedding_service

    @property
    def embedding_service(self) -> EmbeddingService:
        """Get the embedding service (lazy initialization)."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    def find_similar_summaries(
        self,
        embedding: list[float],
        limit: int = 5,
        exclude_idea_id: str | None = None,
    ) -> list[SimilarIdea]:
        """Find ideas with similar summaries.

        Args:
            embedding: The embedding vector to compare against.
            limit: Maximum number of results to return.
            exclude_idea_id: Optional idea ID to exclude from results.

        Returns:
            List of SimilarIdea results sorted by similarity (highest first).
        """
        query = """
        SELECT
            i.id,
            i.title,
            1 - array_cosine_distance(s.embedding, ?::FLOAT[768]) as similarity
        FROM summaries s
        JOIN ideas i ON s.idea_id = i.id
        WHERE s.embedding IS NOT NULL
        """
        params = [embedding]

        if exclude_idea_id:
            query += " AND i.id != ?"
            params.append(exclude_idea_id)

        query += """
        ORDER BY similarity DESC
        LIMIT ?
        """
        params.append(limit)

        rows = fetchall(query, params)
        return [
            SimilarIdea(idea_id=row[0], title=row[1], similarity=row[2])
            for row in rows
        ]

    def find_similar_challenges(
        self,
        embedding: list[float],
        limit: int = 5,
        exclude_idea_id: str | None = None,
    ) -> list[SimilarIdea]:
        """Find ideas with similar challenges.

        Args:
            embedding: The embedding vector to compare against.
            limit: Maximum number of results to return.
            exclude_idea_id: Optional idea ID to exclude from results.

        Returns:
            List of SimilarIdea results sorted by similarity (highest first).
        """
        query = """
        SELECT
            i.id,
            i.title,
            1 - array_cosine_distance(c.embedding, ?::FLOAT[768]) as similarity
        FROM challenges c
        JOIN ideas i ON c.idea_id = i.id
        WHERE c.embedding IS NOT NULL
        """
        params = [embedding]

        if exclude_idea_id:
            query += " AND i.id != ?"
            params.append(exclude_idea_id)

        query += """
        ORDER BY similarity DESC
        LIMIT ?
        """
        params.append(limit)

        rows = fetchall(query, params)
        return [
            SimilarIdea(idea_id=row[0], title=row[1], similarity=row[2])
            for row in rows
        ]

    def find_similar_approaches(
        self,
        embedding: list[float],
        limit: int = 5,
        exclude_idea_id: str | None = None,
    ) -> list[SimilarIdea]:
        """Find ideas with similar approaches.

        Args:
            embedding: The embedding vector to compare against.
            limit: Maximum number of results to return.
            exclude_idea_id: Optional idea ID to exclude from results.

        Returns:
            List of SimilarIdea results sorted by similarity (highest first).
        """
        query = """
        SELECT
            i.id,
            i.title,
            1 - array_cosine_distance(a.embedding, ?::FLOAT[768]) as similarity
        FROM approaches a
        JOIN ideas i ON a.idea_id = i.id
        WHERE a.embedding IS NOT NULL
        """
        params = [embedding]

        if exclude_idea_id:
            query += " AND i.id != ?"
            params.append(exclude_idea_id)

        query += """
        ORDER BY similarity DESC
        LIMIT ?
        """
        params.append(limit)

        rows = fetchall(query, params)
        return [
            SimilarIdea(idea_id=row[0], title=row[1], similarity=row[2])
            for row in rows
        ]

    def find_similar_for_idea(
        self,
        idea_id: str,
        limit: int = 5,
    ) -> list[SimilarIdea]:
        """Find ideas similar to a given idea.

        Uses the idea's summary embedding if available, otherwise generates one.
        Excludes the input idea from results.

        Args:
            idea_id: The ID of the idea to find similar ideas for.
            limit: Maximum number of results to return.

        Returns:
            List of SimilarIdea results sorted by similarity (highest first).
        """
        # Get the idea's summary embedding
        row = fetchone(
            """
            SELECT embedding, content FROM summaries WHERE idea_id = ?
            """,
            [idea_id],
        )

        if not row:
            logger.warning(f"No summary found for idea {idea_id}")
            return []

        embedding, content = row

        # If no embedding yet, generate one
        if embedding is None:
            if not content:
                logger.warning(f"No content for summary of idea {idea_id}")
                return []
            embedding = self.embedding_service.embed(content)

        return self.find_similar_summaries(
            embedding=embedding,
            limit=limit,
            exclude_idea_id=idea_id,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Objective Similarity (V2)
    # ─────────────────────────────────────────────────────────────────────────

    def find_similar_objectives(
        self,
        embedding: list[float],
        limit: int = 5,
        exclude_id: str | None = None,
        active_only: bool = True,
    ) -> list[SimilarObjective]:
        """Find objectives with similar descriptions.

        Args:
            embedding: The embedding vector to compare against.
            limit: Maximum number of results to return.
            exclude_id: Optional objective ID to exclude from results.
            active_only: If True, only return active objectives.

        Returns:
            List of SimilarObjective results sorted by similarity (highest first).
        """
        query = """
        SELECT
            o.id,
            o.title,
            1 - array_cosine_distance(o.embedding, ?::FLOAT[768]) as similarity
        FROM objectives o
        WHERE o.embedding IS NOT NULL
        """
        params = [embedding]

        if active_only:
            query += " AND o.status = 'Active'"

        if exclude_id:
            query += " AND o.id != ?"
            params.append(exclude_id)

        query += """
        ORDER BY similarity DESC
        LIMIT ?
        """
        params.append(limit)

        rows = fetchall(query, params)
        return [
            SimilarObjective(objective_id=row[0], title=row[1], similarity=row[2])
            for row in rows
        ]

    def find_similar_for_objective(
        self,
        objective_id: str,
        limit: int = 5,
    ) -> list[SimilarObjective]:
        """Find objectives similar to a given objective.

        Uses the objective's embedding if available, otherwise generates one.
        Excludes the input objective from results.

        Args:
            objective_id: The ID of the objective to find similar objectives for.
            limit: Maximum number of results to return.

        Returns:
            List of SimilarObjective results sorted by similarity (highest first).
        """
        # Get the objective's embedding
        row = fetchone(
            """
            SELECT embedding, description FROM objectives WHERE id = ?
            """,
            [objective_id],
        )

        if not row:
            logger.warning(f"No objective found with id {objective_id}")
            return []

        embedding, description = row

        # If no embedding yet, generate one
        if embedding is None:
            if not description:
                logger.warning(f"No description for objective {objective_id}")
                return []
            embedding = self.embedding_service.embed(description)

        return self.find_similar_objectives(
            embedding=embedding,
            limit=limit,
            exclude_id=objective_id,
        )
