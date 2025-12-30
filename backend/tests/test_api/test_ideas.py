"""Tests for Ideas API endpoints.

Tests cover CRUD operations for ideas.
"""

import pytest


class TestListIdeas:
    """Tests for GET /api/ideas."""

    def test_list_ideas_empty(self, authenticated_client):
        """List returns empty array when no ideas exist."""
        response = authenticated_client.get("/api/ideas")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_ideas_returns_created_ideas(self, authenticated_client):
        """List returns ideas after creation."""
        # Create an idea
        authenticated_client.post(
            "/api/ideas",
            json={"title": "Test Idea", "summary": {"content": "Test summary"}},
        )

        response = authenticated_client.get("/api/ideas")
        assert response.status_code == 200
        ideas = response.json()
        assert len(ideas) >= 1
        assert any(idea["title"] == "Test Idea" for idea in ideas)

    def test_list_ideas_with_author_filter(self, authenticated_client):
        """List can filter by author_id."""
        # Create an idea
        create_response = authenticated_client.post(
            "/api/ideas",
            json={"title": "Author Filter Test", "summary": {"content": "Test"}},
        )
        author_id = create_response.json()["author_id"]

        response = authenticated_client.get(
            "/api/ideas", params={"author_id": author_id}
        )
        assert response.status_code == 200
        ideas = response.json()
        assert all(idea["author_id"] == author_id for idea in ideas)

    def test_list_ideas_with_status_filter(self, authenticated_client):
        """List can filter by status."""
        # Create an idea (default status is 'Draft')
        authenticated_client.post(
            "/api/ideas",
            json={"title": "Status Filter Test", "summary": {"content": "Test"}},
        )

        response = authenticated_client.get("/api/ideas", params={"status": "Draft"})
        assert response.status_code == 200
        ideas = response.json()
        assert all(idea["status"] == "Draft" for idea in ideas)


class TestCreateIdea:
    """Tests for POST /api/ideas."""

    def test_create_idea_success(self, authenticated_client):
        """Create idea returns full detail response."""
        response = authenticated_client.post(
            "/api/ideas",
            json={"title": "New Test Idea", "summary": {"content": "A test summary"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Test Idea"
        assert data["id"] is not None
        assert data["summary"]["content"] == "A test summary"
        assert data["status"] == "Draft"

    def test_create_idea_sets_author(self, authenticated_client):
        """Created idea has correct author."""
        response = authenticated_client.post(
            "/api/ideas",
            json={"title": "Author Test", "summary": {"content": "Test"}},
        )

        data = response.json()
        # Should have a valid author_id (current mock user)
        assert data["author_id"] is not None
        assert len(data["author_id"]) > 0

    def test_create_idea_requires_title(self, authenticated_client):
        """Create fails without title."""
        response = authenticated_client.post(
            "/api/ideas",
            json={"summary": {"content": "Test"}},
        )
        assert response.status_code == 422

    def test_create_idea_requires_summary(self, authenticated_client):
        """Create fails without summary."""
        response = authenticated_client.post(
            "/api/ideas",
            json={"title": "No Summary"},
        )
        assert response.status_code == 422


class TestGetIdea:
    """Tests for GET /api/ideas/{idea_id}."""

    def test_get_idea_success(self, authenticated_client, created_idea):
        """Get returns full idea detail."""
        response = authenticated_client.get(f"/api/ideas/{created_idea}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_idea
        assert "title" in data
        assert "summary" in data

    def test_get_idea_not_found(self, authenticated_client):
        """Get returns 404 for nonexistent idea."""
        response = authenticated_client.get("/api/ideas/nonexistent-id")
        assert response.status_code == 404

    def test_get_idea_includes_components(self, authenticated_client, created_idea):
        """Get includes all idea components."""
        # Add challenge
        authenticated_client.post(
            f"/api/ideas/{created_idea}/challenge",
            json={"content": "Test challenge"},
        )

        response = authenticated_client.get(f"/api/ideas/{created_idea}")
        data = response.json()

        assert data["summary"] is not None
        assert data["challenge"]["content"] == "Test challenge"


class TestUpdateIdea:
    """Tests for PATCH /api/ideas/{idea_id}."""

    def test_update_idea_title(self, authenticated_client, created_idea):
        """Update changes title."""
        response = authenticated_client.patch(
            f"/api/ideas/{created_idea}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_idea_status(self, authenticated_client, created_idea):
        """Update changes status."""
        response = authenticated_client.patch(
            f"/api/ideas/{created_idea}",
            json={"status": "Active"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"

    def test_update_idea_not_found(self, authenticated_client):
        """Update returns 404 for nonexistent idea."""
        response = authenticated_client.patch(
            "/api/ideas/nonexistent-id",
            json={"title": "New Title"},
        )
        assert response.status_code == 404


class TestDeleteIdea:
    """Tests for DELETE /api/ideas/{idea_id}."""

    def test_delete_idea_success(self, authenticated_client, created_idea):
        """Delete removes idea."""
        response = authenticated_client.delete(f"/api/ideas/{created_idea}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify it's gone
        get_response = authenticated_client.get(f"/api/ideas/{created_idea}")
        assert get_response.status_code == 404

    def test_delete_idea_not_found(self, authenticated_client):
        """Delete returns 404 for nonexistent idea."""
        response = authenticated_client.delete("/api/ideas/nonexistent-id")
        assert response.status_code == 404


class TestSimilarIdeas:
    """Tests for GET /api/ideas/{idea_id}/similar."""

    def test_similar_ideas_returns_list(self, authenticated_client, created_idea):
        """Similar ideas endpoint returns list."""
        response = authenticated_client.get(f"/api/ideas/{created_idea}/similar")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_similar_ideas_not_found(self, authenticated_client):
        """Similar ideas returns 404 for nonexistent idea."""
        response = authenticated_client.get("/api/ideas/nonexistent-id/similar")
        assert response.status_code == 404

    def test_similar_ideas_accepts_limit(self, authenticated_client, created_idea):
        """Similar ideas accepts limit parameter."""
        response = authenticated_client.get(
            f"/api/ideas/{created_idea}/similar",
            params={"limit": 3},
        )
        assert response.status_code == 200
