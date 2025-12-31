"""Graph batch job - rebuilds similarity edges from relationships table.

This batch job periodically processes the relationships table (populated by
ConnectionAgent signals) and materializes them into the graph_similar_* tables
for efficient graph traversal.

Run periodically (e.g., every 5 minutes) or on-demand after bulk operations.
"""

import logging
from datetime import datetime

from crabgrass.database import execute, fetchall

logger = logging.getLogger(__name__)

# Minimum similarity score to create a graph edge
MIN_SIMILARITY_SCORE = 0.6


class GraphBatchJob:
    """Batch job for building and maintaining graph similarity edges."""

    def __init__(self, min_score: float = MIN_SIMILARITY_SCORE):
        """Initialize batch job.

        Args:
            min_score: Minimum similarity score to include (default 0.6)
        """
        self.min_score = min_score

    def run(self) -> dict:
        """Run the full batch job.

        Returns:
            Dict with counts of edges created/updated for each type
        """
        logger.info("GraphBatchJob: Starting similarity edge rebuild")
        start_time = datetime.utcnow()

        results = {
            "idea_edges": self._rebuild_idea_edges(),
            "challenge_edges": self._rebuild_challenge_edges(),
            "approach_edges": self._rebuild_approach_edges(),
            "duration_ms": 0,
        }

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        results["duration_ms"] = int(duration)

        logger.info(
            f"GraphBatchJob: Complete - {results['idea_edges']} idea edges, "
            f"{results['challenge_edges']} challenge edges, "
            f"{results['approach_edges']} approach edges "
            f"({results['duration_ms']}ms)"
        )

        return results

    def _rebuild_idea_edges(self) -> int:
        """Rebuild graph_similar_ideas from relationships table.

        Returns:
            Number of edges created/updated
        """
        # Clear existing edges (full rebuild approach)
        execute("DELETE FROM graph_similar_ideas")

        # Get idea-to-idea similarity relationships
        rows = fetchall(
            """
            SELECT
                from_id,
                to_id,
                score,
                from_type as match_type,
                discovered_at
            FROM relationships
            WHERE relationship = 'similar'
              AND from_type IN ('idea', 'summary', 'challenge', 'approach')
              AND to_type IN ('idea', 'summary', 'challenge', 'approach')
              AND score >= ?
            """,
            [self.min_score],
        )

        count = 0
        for from_id, to_id, score, match_type, discovered_at in rows:
            # Get idea IDs from component IDs if needed
            from_idea_id = self._get_idea_id(from_id, match_type)
            to_idea_id = self._get_idea_id(to_id, match_type)

            if from_idea_id and to_idea_id and from_idea_id != to_idea_id:
                try:
                    execute(
                        """
                        INSERT INTO graph_similar_ideas
                            (from_idea_id, to_idea_id, similarity_score, match_type, discovered_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT (from_idea_id, to_idea_id, match_type) DO UPDATE
                        SET similarity_score = EXCLUDED.similarity_score,
                            discovered_at = EXCLUDED.discovered_at
                        """,
                        [from_idea_id, to_idea_id, score, match_type, discovered_at],
                    )
                    count += 1
                except Exception as e:
                    logger.debug(f"Error inserting idea edge: {e}")

        logger.debug(f"GraphBatchJob: Created {count} idea similarity edges")
        return count

    def _rebuild_challenge_edges(self) -> int:
        """Rebuild graph_similar_challenges from relationships table.

        Returns:
            Number of edges created/updated
        """
        execute("DELETE FROM graph_similar_challenges")

        rows = fetchall(
            """
            SELECT
                from_id,
                to_id,
                score,
                discovered_at
            FROM relationships
            WHERE relationship = 'similar'
              AND from_type = 'challenge'
              AND to_type = 'challenge'
              AND score >= ?
            """,
            [self.min_score],
        )

        count = 0
        for from_id, to_id, score, discovered_at in rows:
            if from_id != to_id:
                try:
                    execute(
                        """
                        INSERT INTO graph_similar_challenges
                            (from_challenge_id, to_challenge_id, similarity_score, discovered_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT (from_challenge_id, to_challenge_id) DO UPDATE
                        SET similarity_score = EXCLUDED.similarity_score,
                            discovered_at = EXCLUDED.discovered_at
                        """,
                        [from_id, to_id, score, discovered_at],
                    )
                    count += 1
                except Exception as e:
                    logger.debug(f"Error inserting challenge edge: {e}")

        logger.debug(f"GraphBatchJob: Created {count} challenge similarity edges")
        return count

    def _rebuild_approach_edges(self) -> int:
        """Rebuild graph_similar_approaches from relationships table.

        Returns:
            Number of edges created/updated
        """
        execute("DELETE FROM graph_similar_approaches")

        rows = fetchall(
            """
            SELECT
                from_id,
                to_id,
                score,
                discovered_at
            FROM relationships
            WHERE relationship = 'similar'
              AND from_type = 'approach'
              AND to_type = 'approach'
              AND score >= ?
            """,
            [self.min_score],
        )

        count = 0
        for from_id, to_id, score, discovered_at in rows:
            if from_id != to_id:
                try:
                    execute(
                        """
                        INSERT INTO graph_similar_approaches
                            (from_approach_id, to_approach_id, similarity_score, discovered_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT (from_approach_id, to_approach_id) DO UPDATE
                        SET similarity_score = EXCLUDED.similarity_score,
                            discovered_at = EXCLUDED.discovered_at
                        """,
                        [from_id, to_id, score, discovered_at],
                    )
                    count += 1
                except Exception as e:
                    logger.debug(f"Error inserting approach edge: {e}")

        logger.debug(f"GraphBatchJob: Created {count} approach similarity edges")
        return count

    def _get_idea_id(self, component_id: str, component_type: str) -> str | None:
        """Get idea ID from a component ID.

        Args:
            component_id: The ID of the component (could be idea, summary, challenge, approach)
            component_type: The type of component

        Returns:
            The idea ID, or None if not found
        """
        if component_type == "idea":
            return component_id

        table_map = {
            "summary": "summaries",
            "challenge": "challenges",
            "approach": "approaches",
        }

        table = table_map.get(component_type)
        if not table:
            return None

        row = fetchall(
            f"SELECT idea_id FROM {table} WHERE id = ?",
            [component_id],
        )

        if row:
            return row[0][0]
        return None

    def rebuild_objective_hierarchy(self) -> int:
        """Rebuild objective hierarchy edges from parent_id relationships.

        Returns:
            Number of edges created
        """
        logger.info("GraphBatchJob: Rebuilding objective hierarchy")

        # Clear existing hierarchy
        execute("DELETE FROM graph_objective_hierarchy")

        # Get all objectives with parents
        objectives = fetchall(
            """
            SELECT id, parent_id
            FROM objectives
            WHERE parent_id IS NOT NULL
            """
        )

        count = 0
        now = datetime.utcnow()

        for obj_id, parent_id in objectives:
            # Add direct edge
            execute(
                """
                INSERT INTO graph_objective_hierarchy (parent_id, child_id, depth, created_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT (parent_id, child_id) DO NOTHING
                """,
                [parent_id, obj_id, now],
            )
            count += 1

            # Add transitive edges (ancestors)
            # Walk up the tree
            current_parent = parent_id
            depth = 2
            visited = {obj_id, parent_id}

            while current_parent:
                row = fetchall(
                    "SELECT parent_id FROM objectives WHERE id = ?",
                    [current_parent],
                )

                if not row or not row[0][0]:
                    break

                grandparent = row[0][0]
                if grandparent in visited:
                    break  # Cycle detection

                visited.add(grandparent)

                execute(
                    """
                    INSERT INTO graph_objective_hierarchy (parent_id, child_id, depth, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT (parent_id, child_id) DO NOTHING
                    """,
                    [grandparent, obj_id, depth, now],
                )
                count += 1
                current_parent = grandparent
                depth += 1

        logger.info(f"GraphBatchJob: Created {count} objective hierarchy edges")
        return count


def run_graph_batch():
    """Convenience function to run the batch job."""
    job = GraphBatchJob()
    return job.run()
