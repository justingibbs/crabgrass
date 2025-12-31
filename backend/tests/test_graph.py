"""Tests for graph layer functionality.

Tests cover:
1. Graph edge tables and schema
2. Graph sync handlers (objective hierarchy)
3. GraphService traversal methods
4. Hybrid search capabilities
5. Graph batch job
"""

import pytest
from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────────────────────────────────────────
# Graph Schema Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGraphSchema:
    """Tests for graph edge table schema."""

    def test_graph_similar_ideas_table_exists(self, test_db):
        """graph_similar_ideas table should exist."""
        from crabgrass.database import fetchall

        tables = fetchall(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'graph_similar_ideas'"
        )
        assert len(tables) == 1

    def test_graph_similar_challenges_table_exists(self, test_db):
        """graph_similar_challenges table should exist."""
        from crabgrass.database import fetchall

        tables = fetchall(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'graph_similar_challenges'"
        )
        assert len(tables) == 1

    def test_graph_similar_approaches_table_exists(self, test_db):
        """graph_similar_approaches table should exist."""
        from crabgrass.database import fetchall

        tables = fetchall(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'graph_similar_approaches'"
        )
        assert len(tables) == 1

    def test_graph_objective_hierarchy_table_exists(self, test_db):
        """graph_objective_hierarchy table should exist."""
        from crabgrass.database import fetchall

        tables = fetchall(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'graph_objective_hierarchy'"
        )
        assert len(tables) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Graph Handler Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGraphHandlers:
    """Tests for graph sync handlers."""

    def test_update_objective_hierarchy_creates_edge(self, test_db):
        """update_objective_hierarchy should create hierarchy edge."""
        from crabgrass.syncs.handlers.graph import update_objective_hierarchy
        from crabgrass.database import fetchall

        # Create hierarchy edge
        update_objective_hierarchy(
            sender=None,
            objective_id="child-obj",
            parent_id="parent-obj",
        )

        # Verify edge was created
        edges = fetchall(
            "SELECT parent_id, child_id, depth FROM graph_objective_hierarchy WHERE child_id = ?",
            ["child-obj"],
        )

        assert len(edges) == 1
        assert edges[0][0] == "parent-obj"
        assert edges[0][1] == "child-obj"
        assert edges[0][2] == 1

    def test_update_objective_hierarchy_removes_old_edges(self, test_db):
        """update_objective_hierarchy should remove old edges when parent changes."""
        from crabgrass.syncs.handlers.graph import update_objective_hierarchy
        from crabgrass.database import fetchall

        # Create initial hierarchy
        update_objective_hierarchy(sender=None, objective_id="child", parent_id="parent1")

        # Change parent
        update_objective_hierarchy(sender=None, objective_id="child", parent_id="parent2")

        # Verify only new edge exists
        edges = fetchall(
            "SELECT parent_id FROM graph_objective_hierarchy WHERE child_id = ?",
            ["child"],
        )

        assert len(edges) == 1
        assert edges[0][0] == "parent2"

    def test_update_objective_hierarchy_no_edge_for_root(self, test_db):
        """update_objective_hierarchy should not create edge for root objective."""
        from crabgrass.syncs.handlers.graph import update_objective_hierarchy
        from crabgrass.database import fetchall

        # Create without parent (root)
        update_objective_hierarchy(sender=None, objective_id="root-obj", parent_id=None)

        # Verify no edges
        edges = fetchall(
            "SELECT * FROM graph_objective_hierarchy WHERE child_id = ?",
            ["root-obj"],
        )

        assert len(edges) == 0


# ─────────────────────────────────────────────────────────────────────────────
# GraphService Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGraphService:
    """Tests for GraphService methods."""

    def test_get_similar_ideas_returns_matches(self, test_db):
        """get_similar_ideas should return similar ideas from graph."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.database import execute
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions

        # Setup: Create ideas and graph edges
        UserActions.ensure_mock_users_exist()
        idea1 = IdeaActions.create(title="Source Idea", author_id="sarah-001")
        idea2 = IdeaActions.create(title="Similar Idea", author_id="sarah-001")

        # Insert similarity edge
        execute(
            """
            INSERT INTO graph_similar_ideas
                (from_idea_id, to_idea_id, similarity_score, match_type)
            VALUES (?, ?, ?, ?)
            """,
            [idea1.id, idea2.id, 0.85, "summary"],
        )

        # Test
        service = get_graph_service()
        matches = service.get_similar_ideas(idea1.id)

        assert len(matches) == 1
        assert matches[0].idea_id == idea2.id
        assert abs(matches[0].similarity - 0.85) < 0.001  # Float comparison
        assert matches[0].match_type == "summary"

    def test_get_similar_ideas_respects_min_score(self, test_db):
        """get_similar_ideas should filter by min_score."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.database import execute
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()
        idea1 = IdeaActions.create(title="Source", author_id="sarah-001")
        idea2 = IdeaActions.create(title="Low Match", author_id="sarah-001")

        execute(
            """
            INSERT INTO graph_similar_ideas
                (from_idea_id, to_idea_id, similarity_score, match_type)
            VALUES (?, ?, ?, ?)
            """,
            [idea1.id, idea2.id, 0.4, "summary"],  # Below default threshold
        )

        service = get_graph_service()
        matches = service.get_similar_ideas(idea1.id, min_score=0.5)

        assert len(matches) == 0

    def test_get_ideas_for_objective(self, test_db):
        """get_ideas_for_objective should return linked ideas."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.objective import ObjectiveActions
        from crabgrass.concepts.idea_objective import IdeaObjectiveActions
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()
        idea = IdeaActions.create(title="Test Idea", author_id="sarah-001")
        objective = ObjectiveActions.create(
            title="Test Objective",
            description="Description",
            author_id="sarah-001",
        )
        IdeaObjectiveActions.link(idea.id, objective.id)

        service = get_graph_service()
        idea_ids = service.get_ideas_for_objective(objective.id)

        assert idea.id in idea_ids

    def test_get_user_graph_scope(self, test_db):
        """get_user_graph_scope should return user's accessible ideas."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()
        idea = IdeaActions.create(title="User's Idea", author_id="sarah-001")

        service = get_graph_service()
        scope = service.get_user_graph_scope("sarah-001")

        assert idea.id in scope["idea_ids"]

    def test_get_objectives_for_idea(self, test_db):
        """get_objectives_for_idea should return linked objectives."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.objective import ObjectiveActions
        from crabgrass.concepts.idea_objective import IdeaObjectiveActions
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()
        idea = IdeaActions.create(title="Test Idea", author_id="sarah-001")
        objective = ObjectiveActions.create(
            title="Linked Objective",
            description="Description",
            author_id="sarah-001",
        )
        IdeaObjectiveActions.link(idea.id, objective.id)

        service = get_graph_service()
        objectives = service.get_objectives_for_idea(idea.id)

        assert len(objectives) == 1
        assert objectives[0]["id"] == objective.id
        assert objectives[0]["title"] == "Linked Objective"


# ─────────────────────────────────────────────────────────────────────────────
# Graph Batch Job Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGraphBatchJob:
    """Tests for GraphBatchJob."""

    def test_run_returns_counts(self, test_db):
        """run() should return edge counts."""
        from crabgrass.services.graph_batch import GraphBatchJob

        job = GraphBatchJob()
        result = job.run()

        assert "idea_edges" in result
        assert "challenge_edges" in result
        assert "approach_edges" in result
        assert "duration_ms" in result

    def test_rebuild_objective_hierarchy(self, test_db):
        """rebuild_objective_hierarchy should create edges from parent_id."""
        from crabgrass.services.graph_batch import GraphBatchJob
        from crabgrass.concepts.objective import ObjectiveActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.database import fetchall

        UserActions.ensure_mock_users_exist()

        # Create hierarchy
        parent = ObjectiveActions.create(
            title="Parent",
            description="Parent objective",
            author_id="sarah-001",
        )
        child = ObjectiveActions.create(
            title="Child",
            description="Child objective",
            author_id="sarah-001",
            parent_id=parent.id,
        )

        # Clear hierarchy table (in case sync handler already populated it)
        from crabgrass.database import execute
        execute("DELETE FROM graph_objective_hierarchy")

        # Run batch job
        job = GraphBatchJob()
        count = job.rebuild_objective_hierarchy()

        assert count >= 1

        # Verify edge exists
        edges = fetchall(
            "SELECT parent_id, child_id FROM graph_objective_hierarchy WHERE child_id = ?",
            [child.id],
        )
        assert len(edges) >= 1
        assert any(e[0] == parent.id for e in edges)

    def test_rebuild_idea_edges_from_relationships(self, test_db):
        """rebuild should create graph edges from relationships table."""
        from crabgrass.services.graph_batch import GraphBatchJob
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.database import execute, fetchall
        from datetime import datetime

        UserActions.ensure_mock_users_exist()
        idea1 = IdeaActions.create(title="Idea 1", author_id="sarah-001")
        idea2 = IdeaActions.create(title="Idea 2", author_id="sarah-001")

        # Insert relationship
        execute(
            """
            INSERT INTO relationships
                (id, from_type, from_id, to_type, to_id, relationship, score, discovered_at)
            VALUES (?, ?, ?, ?, ?, 'similar', ?, ?)
            """,
            ["rel-1", "idea", idea1.id, "idea", idea2.id, 0.75, datetime.utcnow()],
        )

        # Run batch job
        job = GraphBatchJob(min_score=0.6)
        result = job.run()

        assert result["idea_edges"] >= 1

        # Verify edge was created
        edges = fetchall(
            "SELECT to_idea_id, similarity_score FROM graph_similar_ideas WHERE from_idea_id = ?",
            [idea1.id],
        )
        assert len(edges) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Objective Hierarchy Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestObjectiveHierarchy:
    """Tests for objective hierarchy queries."""

    def test_get_objective_ancestors(self, test_db):
        """get_objective_ancestors should return parent chain."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.database import execute
        from datetime import datetime

        # Create hierarchy edges manually
        now = datetime.utcnow()
        execute(
            """
            INSERT INTO graph_objective_hierarchy (parent_id, child_id, depth, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ["grandparent", "parent", 1, now],
        )
        execute(
            """
            INSERT INTO graph_objective_hierarchy (parent_id, child_id, depth, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ["parent", "child", 1, now],
        )
        execute(
            """
            INSERT INTO graph_objective_hierarchy (parent_id, child_id, depth, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ["grandparent", "child", 2, now],
        )

        # Create mock objectives
        execute(
            """
            INSERT INTO objectives (id, title, description, status, author_id, created_at, updated_at)
            VALUES (?, ?, ?, 'Active', 'sarah-001', ?, ?)
            """,
            ["grandparent", "Grandparent Obj", "Desc", now, now],
        )
        execute(
            """
            INSERT INTO objectives (id, title, description, status, author_id, parent_id, created_at, updated_at)
            VALUES (?, ?, ?, 'Active', 'sarah-001', ?, ?, ?)
            """,
            ["parent", "Parent Obj", "Desc", "grandparent", now, now],
        )

        service = get_graph_service()
        ancestors = service.get_objective_ancestors("child")

        assert len(ancestors) == 2
        # Sorted by depth (closest first)
        assert ancestors[0]["depth"] == 1
        assert ancestors[1]["depth"] == 2

    def test_get_objective_descendants(self, test_db):
        """get_objective_descendants should return children chain."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.database import execute
        from datetime import datetime

        now = datetime.utcnow()

        # Create objectives
        execute(
            """
            INSERT INTO objectives (id, title, description, status, author_id, created_at, updated_at)
            VALUES (?, ?, ?, 'Active', 'sarah-001', ?, ?)
            """,
            ["root", "Root Obj", "Desc", now, now],
        )
        execute(
            """
            INSERT INTO objectives (id, title, description, status, author_id, parent_id, created_at, updated_at)
            VALUES (?, ?, ?, 'Active', 'sarah-001', ?, ?, ?)
            """,
            ["child1", "Child 1", "Desc", "root", now, now],
        )

        # Create hierarchy edges
        execute(
            """
            INSERT INTO graph_objective_hierarchy (parent_id, child_id, depth, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ["root", "child1", 1, now],
        )

        service = get_graph_service()
        descendants = service.get_objective_descendants("root")

        assert len(descendants) >= 1
        assert any(d["id"] == "child1" for d in descendants)


# ─────────────────────────────────────────────────────────────────────────────
# Hybrid Search Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestHybridSearch:
    """Tests for hybrid vector + graph search."""

    def test_find_similar_within_scope(self, test_db, mock_embedding_service):
        """find_similar_within_scope should filter to scoped ideas."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.summary import SummaryActions
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()

        # Create ideas with embeddings
        idea1 = IdeaActions.create(title="In Scope", author_id="sarah-001")
        idea2 = IdeaActions.create(title="Out of Scope", author_id="mike-001")

        # Add summaries with embeddings
        summary1 = SummaryActions.get_by_idea_id(idea1.id)
        summary2 = SummaryActions.get_by_idea_id(idea2.id)

        # Mock embeddings
        query_embedding = [0.1] * 768

        service = get_graph_service()

        # Scope to only idea1
        matches = service.find_similar_within_scope(
            embedding=query_embedding,
            scope_idea_ids={idea1.id},
            content_type="summary",
            limit=10,
        )

        # Should only include idea1
        match_ids = [m.idea_id for m in matches]
        assert idea2.id not in match_ids

    def test_hybrid_search_with_user(self, test_db, mock_embedding_service):
        """hybrid_search should boost results for user's graph."""
        from crabgrass.services.graph import get_graph_service
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()
        idea = IdeaActions.create(title="User's Idea", author_id="sarah-001")

        query_embedding = [0.1] * 768

        service = get_graph_service()
        matches = service.hybrid_search(
            embedding=query_embedding,
            user_id="sarah-001",
            content_type="summary",
            limit=10,
        )

        # Should return results (even if similarity is based on mock embeddings)
        # The test mainly verifies the method doesn't crash
        assert isinstance(matches, list)


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoint Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGraphAPI:
    """Tests for graph API endpoints."""

    def test_get_similar_ideas_endpoint(self, client, test_db):
        """GET /api/graph/ideas/{id}/similar should return matches."""
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions
        from crabgrass.database import execute

        UserActions.ensure_mock_users_exist()
        idea1 = IdeaActions.create(title="Source", author_id="sarah-001")
        idea2 = IdeaActions.create(title="Similar", author_id="sarah-001")

        execute(
            """
            INSERT INTO graph_similar_ideas
                (from_idea_id, to_idea_id, similarity_score, match_type)
            VALUES (?, ?, ?, ?)
            """,
            [idea1.id, idea2.id, 0.8, "summary"],
        )

        response = client.get(f"/api/graph/ideas/{idea1.id}/similar")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1
        assert data[0]["idea_id"] == idea2.id

    def test_get_objective_tree_endpoint(self, client, test_db):
        """GET /api/graph/objectives/{id}/tree should return tree."""
        from crabgrass.concepts.objective import ObjectiveActions
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()
        objective = ObjectiveActions.create(
            title="Root Objective",
            description="Description",
            author_id="sarah-001",
        )

        response = client.get(f"/api/graph/objectives/{objective.id}/tree")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == objective.id
        assert data["title"] == "Root Objective"
        assert "children" in data

    def test_get_user_graph_scope_endpoint(self, client, test_db):
        """GET /api/graph/users/{id}/graph-scope should return scope."""
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions

        UserActions.ensure_mock_users_exist()
        idea = IdeaActions.create(title="User Idea", author_id="sarah-001")

        response = client.get("/api/graph/users/sarah-001/graph-scope")
        assert response.status_code == 200

        data = response.json()
        assert idea.id in data["idea_ids"]

    def test_rebuild_graph_endpoint(self, client, test_db):
        """POST /api/graph/admin/rebuild-graph should run batch job."""
        response = client.post("/api/graph/admin/rebuild-graph")
        assert response.status_code == 200

        data = response.json()
        assert "idea_edges" in data
        assert "duration_ms" in data


# ─────────────────────────────────────────────────────────────────────────────
# Registry Integration Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGraphRegistryIntegration:
    """Tests for graph handler registration in registry."""

    def test_update_objective_hierarchy_in_registry(self):
        """update_objective_hierarchy should be in registry."""
        from crabgrass.syncs.registry import SYNCHRONIZATIONS

        assert "update_objective_hierarchy" in SYNCHRONIZATIONS["objective.created"]
        assert "update_objective_hierarchy" in SYNCHRONIZATIONS["objective.updated"]

    def test_record_similarity_edge_in_registry(self):
        """record_similarity_edge should be in registry."""
        from crabgrass.syncs.registry import SYNCHRONIZATIONS

        assert "record_similarity_edge" in SYNCHRONIZATIONS["agent.found_similarity"]

    def test_graph_handlers_registered(self):
        """Graph handlers should be in HANDLERS dict."""
        from crabgrass.syncs.handlers import HANDLERS

        assert "update_objective_hierarchy" in HANDLERS
        assert "record_similarity_edge" in HANDLERS
