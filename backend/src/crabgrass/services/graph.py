"""Graph service - traversal and hybrid queries.

This service provides graph traversal capabilities and hybrid queries that
combine vector similarity with graph relationships.

Key capabilities:
- Traverse idea relationships (similar ideas, linked objectives)
- Scope vector searches to user's graph (their ideas, watched objectives)
- Multi-hop queries (find approaches → get their challenges → analyze)
- Hybrid ranking (combine similarity score with graph distance)
"""

import logging
from dataclasses import dataclass
from typing import Literal

from crabgrass.database import fetchall

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """A node in the graph."""

    id: str
    type: str  # 'idea', 'objective', 'user', 'challenge', 'approach', 'summary'
    title: str | None = None
    properties: dict | None = None


@dataclass
class GraphEdge:
    """An edge in the graph."""

    from_id: str
    to_id: str
    relationship: str
    properties: dict | None = None


@dataclass
class SimilarityMatch:
    """A similarity match with optional graph context."""

    idea_id: str
    title: str
    similarity: float
    match_type: str  # 'summary', 'challenge', 'approach'
    graph_distance: int | None = None  # hops from source in graph
    shared_objectives: list[str] | None = None


@dataclass
class HybridMatch:
    """Result from hybrid vector+graph query."""

    idea_id: str
    title: str
    similarity_score: float
    graph_score: float
    combined_score: float
    match_type: str
    path: list[str] | None = None  # Graph path from query source


class GraphService:
    """Service for graph traversal and hybrid queries."""

    def __init__(self):
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # Basic Traversal
    # ─────────────────────────────────────────────────────────────────────────

    def get_similar_ideas(
        self,
        idea_id: str,
        limit: int = 10,
        min_score: float = 0.5,
    ) -> list[SimilarityMatch]:
        """Get ideas similar to the given idea via graph edges.

        Args:
            idea_id: The source idea ID
            limit: Maximum results to return
            min_score: Minimum similarity score

        Returns:
            List of similar ideas sorted by similarity
        """
        rows = fetchall(
            """
            SELECT
                gsi.to_idea_id,
                i.title,
                gsi.similarity_score,
                gsi.match_type
            FROM graph_similar_ideas gsi
            JOIN ideas i ON gsi.to_idea_id = i.id
            WHERE gsi.from_idea_id = ?
              AND gsi.similarity_score >= ?
            ORDER BY gsi.similarity_score DESC
            LIMIT ?
            """,
            [idea_id, min_score, limit],
        )

        return [
            SimilarityMatch(
                idea_id=row[0],
                title=row[1],
                similarity=row[2],
                match_type=row[3],
            )
            for row in rows
        ]

    def get_ideas_for_objective(
        self,
        objective_id: str,
        include_children: bool = True,
    ) -> list[str]:
        """Get all idea IDs linked to an objective (and optionally its children).

        Args:
            objective_id: The objective to query
            include_children: If True, include ideas linked to child objectives

        Returns:
            List of idea IDs
        """
        if include_children:
            # Use hierarchy graph to get all descendant objectives
            rows = fetchall(
                """
                SELECT DISTINCT io.idea_id
                FROM idea_objectives io
                WHERE io.objective_id = ?
                   OR io.objective_id IN (
                       SELECT child_id FROM graph_objective_hierarchy
                       WHERE parent_id = ?
                   )
                """,
                [objective_id, objective_id],
            )
        else:
            rows = fetchall(
                "SELECT idea_id FROM idea_objectives WHERE objective_id = ?",
                [objective_id],
            )

        return [row[0] for row in rows]

    def get_objectives_for_idea(self, idea_id: str) -> list[dict]:
        """Get all objectives linked to an idea.

        Returns:
            List of dicts with objective_id and title
        """
        rows = fetchall(
            """
            SELECT o.id, o.title, o.status
            FROM idea_objectives io
            JOIN objectives o ON io.objective_id = o.id
            WHERE io.idea_id = ?
            """,
            [idea_id],
        )

        return [
            {"id": row[0], "title": row[1], "status": row[2]}
            for row in rows
        ]

    def get_user_graph_scope(self, user_id: str) -> dict:
        """Get the set of IDs a user has access to via their graph.

        Returns all ideas authored by user, ideas under watched objectives,
        and objectives being watched.

        Args:
            user_id: The user ID

        Returns:
            Dict with 'idea_ids', 'objective_ids' sets
        """
        # User's authored ideas
        authored_ideas = fetchall(
            "SELECT id FROM ideas WHERE author_id = ?",
            [user_id],
        )
        idea_ids = {row[0] for row in authored_ideas}

        # Watched objectives
        watched_objectives = fetchall(
            "SELECT target_id FROM watches WHERE user_id = ? AND target_type = 'objective'",
            [user_id],
        )
        objective_ids = {row[0] for row in watched_objectives}

        # Ideas linked to watched objectives (including children)
        for obj_id in list(objective_ids):
            linked_ideas = self.get_ideas_for_objective(obj_id, include_children=True)
            idea_ids.update(linked_ideas)

        # Watched ideas
        watched_ideas = fetchall(
            "SELECT target_id FROM watches WHERE user_id = ? AND target_type = 'idea'",
            [user_id],
        )
        idea_ids.update(row[0] for row in watched_ideas)

        return {
            "idea_ids": idea_ids,
            "objective_ids": objective_ids,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Graph-Scoped Vector Search
    # ─────────────────────────────────────────────────────────────────────────

    def find_similar_within_scope(
        self,
        embedding: list[float],
        scope_idea_ids: set[str],
        content_type: Literal["summary", "challenge", "approach"] = "summary",
        limit: int = 10,
        min_score: float = 0.5,
    ) -> list[SimilarityMatch]:
        """Find similar content, but only within a set of scoped ideas.

        This enables queries like "find similar approaches, but only within
        ideas linked to objectives I'm watching."

        Args:
            embedding: The query embedding vector
            scope_idea_ids: Set of idea IDs to search within
            content_type: Type of content to search ('summary', 'challenge', 'approach')
            limit: Maximum results
            min_score: Minimum similarity score

        Returns:
            List of matches within scope
        """
        if not scope_idea_ids:
            return []

        # Build the IN clause
        placeholders = ",".join(["?"] * len(scope_idea_ids))

        table_map = {
            "summary": "summaries",
            "challenge": "challenges",
            "approach": "approaches",
        }
        table = table_map.get(content_type, "summaries")

        # Query with vector similarity and scope filter
        query = f"""
            SELECT
                c.idea_id,
                i.title,
                1 - array_cosine_distance(c.embedding, ?::FLOAT[768]) as similarity
            FROM {table} c
            JOIN ideas i ON c.idea_id = i.id
            WHERE c.embedding IS NOT NULL
              AND c.idea_id IN ({placeholders})
            ORDER BY similarity DESC
            LIMIT ?
        """

        params = [embedding] + list(scope_idea_ids) + [limit * 2]  # Over-fetch to filter
        rows = fetchall(query, params)

        results = []
        for row in rows:
            if row[2] >= min_score:
                results.append(
                    SimilarityMatch(
                        idea_id=row[0],
                        title=row[1],
                        similarity=row[2],
                        match_type=content_type,
                    )
                )
                if len(results) >= limit:
                    break

        return results

    def find_similar_for_user(
        self,
        embedding: list[float],
        user_id: str,
        content_type: Literal["summary", "challenge", "approach"] = "summary",
        limit: int = 10,
        min_score: float = 0.5,
    ) -> list[SimilarityMatch]:
        """Find similar content within user's graph scope.

        Combines user's graph scope with vector similarity search.

        Args:
            embedding: The query embedding vector
            user_id: User to scope the search to
            content_type: Type of content to search
            limit: Maximum results
            min_score: Minimum similarity score

        Returns:
            List of matches within user's scope
        """
        scope = self.get_user_graph_scope(user_id)
        return self.find_similar_within_scope(
            embedding=embedding,
            scope_idea_ids=scope["idea_ids"],
            content_type=content_type,
            limit=limit,
            min_score=min_score,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Multi-Hop Queries
    # ─────────────────────────────────────────────────────────────────────────

    def find_similar_approaches_then_challenges(
        self,
        approach_id: str,
        limit: int = 10,
        min_score: float = 0.5,
    ) -> list[dict]:
        """Find similar approaches, then get their parent ideas' challenges.

        Example use case: "I like this approach, show me what challenges
        other people are solving with similar approaches."

        Args:
            approach_id: The source approach
            limit: Maximum results
            min_score: Minimum similarity score for approach match

        Returns:
            List of dicts with challenge info and approach similarity
        """
        # Get similar approaches
        similar_approaches = fetchall(
            """
            SELECT
                gsa.to_approach_id,
                gsa.similarity_score,
                a.idea_id
            FROM graph_similar_approaches gsa
            JOIN approaches a ON gsa.to_approach_id = a.id
            WHERE gsa.from_approach_id = ?
              AND gsa.similarity_score >= ?
            ORDER BY gsa.similarity_score DESC
            LIMIT ?
            """,
            [approach_id, min_score, limit],
        )

        results = []
        for approach_row in similar_approaches:
            target_approach_id = approach_row[0]
            approach_score = approach_row[1]
            target_idea_id = approach_row[2]

            # Get the challenge for this idea
            challenge_rows = fetchall(
                """
                SELECT c.id, c.content, i.title as idea_title
                FROM challenges c
                JOIN ideas i ON c.idea_id = i.id
                WHERE c.idea_id = ?
                LIMIT 1
                """,
                [target_idea_id],
            )

            if challenge_rows:
                results.append({
                    "challenge_id": challenge_rows[0][0],
                    "challenge_content": challenge_rows[0][1],
                    "idea_id": target_idea_id,
                    "idea_title": challenge_rows[0][2],
                    "approach_similarity": approach_score,
                    "source_approach_id": target_approach_id,
                })

        return results

    def find_ideas_with_similar_challenges_different_approaches(
        self,
        idea_id: str,
        limit: int = 10,
        min_score: float = 0.6,
    ) -> list[dict]:
        """Find ideas with similar challenges but different approaches.

        Useful for discovering alternative solutions to the same problem.

        Args:
            idea_id: The source idea
            limit: Maximum results
            min_score: Minimum similarity for challenge match

        Returns:
            List of alternative ideas
        """
        # Get the source idea's challenge
        source_challenge = fetchall(
            "SELECT id, embedding FROM challenges WHERE idea_id = ?",
            [idea_id],
        )

        if not source_challenge or not source_challenge[0][1]:
            return []

        source_challenge_id = source_challenge[0][0]

        # Find ideas with similar challenges
        similar_challenges = fetchall(
            """
            SELECT
                gsc.to_challenge_id,
                gsc.similarity_score,
                c.idea_id,
                i.title
            FROM graph_similar_challenges gsc
            JOIN challenges c ON gsc.to_challenge_id = c.id
            JOIN ideas i ON c.idea_id = i.id
            WHERE gsc.from_challenge_id = ?
              AND gsc.similarity_score >= ?
              AND c.idea_id != ?
            ORDER BY gsc.similarity_score DESC
            LIMIT ?
            """,
            [source_challenge_id, min_score, idea_id, limit * 2],
        )

        results = []
        for row in similar_challenges:
            target_idea_id = row[2]

            # Get the approach for this idea
            approach_rows = fetchall(
                "SELECT id, content FROM approaches WHERE idea_id = ?",
                [target_idea_id],
            )

            if approach_rows:
                results.append({
                    "idea_id": target_idea_id,
                    "idea_title": row[3],
                    "challenge_similarity": row[1],
                    "approach_id": approach_rows[0][0],
                    "approach_preview": approach_rows[0][1][:200] if approach_rows[0][1] else None,
                })

            if len(results) >= limit:
                break

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # Hybrid Ranking
    # ─────────────────────────────────────────────────────────────────────────

    def hybrid_search(
        self,
        embedding: list[float],
        user_id: str | None = None,
        boost_shared_objectives: bool = True,
        content_type: Literal["summary", "challenge", "approach"] = "summary",
        limit: int = 10,
        vector_weight: float = 0.7,
        graph_weight: float = 0.3,
    ) -> list[HybridMatch]:
        """Hybrid search combining vector similarity with graph relationships.

        Boosts results that share objectives or are watched by the user.

        Args:
            embedding: Query embedding
            user_id: Optional user for personalization
            boost_shared_objectives: Boost items sharing objectives with user
            content_type: Type of content to search
            limit: Maximum results
            vector_weight: Weight for vector similarity (0-1)
            graph_weight: Weight for graph proximity (0-1)

        Returns:
            List of hybrid matches sorted by combined score
        """
        table_map = {
            "summary": "summaries",
            "challenge": "challenges",
            "approach": "approaches",
        }
        table = table_map.get(content_type, "summaries")

        # First get vector similarity results
        vector_results = fetchall(
            f"""
            SELECT
                c.idea_id,
                i.title,
                1 - array_cosine_distance(c.embedding, ?::FLOAT[768]) as similarity
            FROM {table} c
            JOIN ideas i ON c.idea_id = i.id
            WHERE c.embedding IS NOT NULL
            ORDER BY similarity DESC
            LIMIT ?
            """,
            [embedding, limit * 3],  # Over-fetch for re-ranking
        )

        if not vector_results:
            return []

        # Get user's graph context for boosting
        user_scope = None
        user_objectives = set()
        if user_id and boost_shared_objectives:
            user_scope = self.get_user_graph_scope(user_id)
            user_objectives = user_scope.get("objective_ids", set())

        results = []
        for row in vector_results:
            idea_id, title, similarity = row[0], row[1], row[2]

            # Calculate graph score
            graph_score = 0.0
            shared_objectives = []

            if user_objectives:
                # Check for shared objectives
                idea_objectives = self.get_objectives_for_idea(idea_id)
                for obj in idea_objectives:
                    if obj["id"] in user_objectives:
                        shared_objectives.append(obj["id"])

                if shared_objectives:
                    graph_score = min(len(shared_objectives) * 0.3, 1.0)

            # Combine scores
            combined = (similarity * vector_weight) + (graph_score * graph_weight)

            results.append(
                HybridMatch(
                    idea_id=idea_id,
                    title=title,
                    similarity_score=similarity,
                    graph_score=graph_score,
                    combined_score=combined,
                    match_type=content_type,
                    path=shared_objectives if shared_objectives else None,
                )
            )

        # Sort by combined score and limit
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[:limit]

    # ─────────────────────────────────────────────────────────────────────────
    # Objective Hierarchy Queries
    # ─────────────────────────────────────────────────────────────────────────

    def get_objective_ancestors(self, objective_id: str) -> list[dict]:
        """Get all ancestor objectives (parents, grandparents, etc).

        Returns:
            List of ancestor objectives ordered by depth (closest first)
        """
        rows = fetchall(
            """
            SELECT o.id, o.title, goh.depth
            FROM graph_objective_hierarchy goh
            JOIN objectives o ON goh.parent_id = o.id
            WHERE goh.child_id = ?
            ORDER BY goh.depth ASC
            """,
            [objective_id],
        )

        return [
            {"id": row[0], "title": row[1], "depth": row[2]}
            for row in rows
        ]

    def get_objective_descendants(self, objective_id: str) -> list[dict]:
        """Get all descendant objectives (children, grandchildren, etc).

        Returns:
            List of descendant objectives ordered by depth
        """
        rows = fetchall(
            """
            SELECT o.id, o.title, goh.depth
            FROM graph_objective_hierarchy goh
            JOIN objectives o ON goh.child_id = o.id
            WHERE goh.parent_id = ?
            ORDER BY goh.depth ASC
            """,
            [objective_id],
        )

        return [
            {"id": row[0], "title": row[1], "depth": row[2]}
            for row in rows
        ]

    def get_objective_tree(self, root_objective_id: str) -> dict:
        """Get the full tree structure under an objective.

        Returns:
            Dict with objective info and nested children
        """
        # Get root info
        root_rows = fetchall(
            "SELECT id, title, status FROM objectives WHERE id = ?",
            [root_objective_id],
        )

        if not root_rows:
            return {}

        root = {
            "id": root_rows[0][0],
            "title": root_rows[0][1],
            "status": root_rows[0][2],
            "children": [],
        }

        # Get direct children
        children_rows = fetchall(
            """
            SELECT o.id, o.title, o.status
            FROM objectives o
            WHERE o.parent_id = ?
            ORDER BY o.title
            """,
            [root_objective_id],
        )

        for child_row in children_rows:
            # Recursively get each child's tree
            child_tree = self.get_objective_tree(child_row[0])
            if child_tree:
                root["children"].append(child_tree)

        return root


# Singleton instance
_graph_service: GraphService | None = None


def get_graph_service() -> GraphService:
    """Get the singleton GraphService instance."""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service
