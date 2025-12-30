"""Tests for Objectives API endpoints."""

import pytest
from unittest.mock import patch, MagicMock


class TestListObjectives:
    """Tests for GET /api/objectives."""

    def test_list_objectives_empty(self, authenticated_client):
        """List returns empty when no objectives exist."""
        response = authenticated_client.get("/api/objectives")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_objectives_returns_created(self, authenticated_client):
        """List returns objectives after creation."""
        # Create an objective
        authenticated_client.post(
            "/api/objectives",
            json={"title": "Test Objective", "description": "Test description"}
        )

        response = authenticated_client.get("/api/objectives")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Objective"

    def test_list_objectives_filters_by_status(self, authenticated_client):
        """List respects status filter."""
        # Create and retire an objective
        resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "To Retire", "description": "Will be retired"}
        )
        obj_id = resp.json()["id"]
        authenticated_client.post(f"/api/objectives/{obj_id}/retire")

        # Create an active objective
        authenticated_client.post(
            "/api/objectives",
            json={"title": "Active One", "description": "Stays active"}
        )

        # Default should return only active
        response = authenticated_client.get("/api/objectives")
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Active One"

        # Explicitly filter retired
        response = authenticated_client.get("/api/objectives?status=Retired")
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "To Retire"


class TestCreateObjective:
    """Tests for POST /api/objectives."""

    def test_create_objective_success(self, authenticated_client):
        """Create objective returns 201 with data."""
        response = authenticated_client.post(
            "/api/objectives",
            json={"title": "New Objective", "description": "Detailed description"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Objective"
        assert data["description"] == "Detailed description"
        assert data["status"] == "Active"
        assert "id" in data

    def test_create_objective_with_parent(self, authenticated_client):
        """Create objective can specify parent."""
        # Create parent
        parent_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Parent", "description": "Parent objective"}
        )
        parent_id = parent_resp.json()["id"]

        # Create child
        response = authenticated_client.post(
            "/api/objectives",
            json={
                "title": "Child",
                "description": "Child objective",
                "parent_id": parent_id,
            }
        )
        assert response.status_code == 201
        assert response.json()["parent_id"] == parent_id

    def test_create_objective_invalid_parent(self, authenticated_client):
        """Create fails with invalid parent ID."""
        response = authenticated_client.post(
            "/api/objectives",
            json={
                "title": "Child",
                "description": "Child objective",
                "parent_id": "nonexistent-id",
            }
        )
        assert response.status_code == 400


class TestGetObjective:
    """Tests for GET /api/objectives/{id}."""

    def test_get_objective_success(self, authenticated_client):
        """Get returns objective detail."""
        # Create objective
        create_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test", "description": "Test description"}
        )
        obj_id = create_resp.json()["id"]

        response = authenticated_client.get(f"/api/objectives/{obj_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == obj_id
        assert data["title"] == "Test"
        assert "idea_count" in data
        assert "sub_objective_count" in data
        assert "is_watched" in data

    def test_get_objective_not_found(self, authenticated_client):
        """Get returns 404 for nonexistent objective."""
        response = authenticated_client.get("/api/objectives/nonexistent-id")
        assert response.status_code == 404


class TestUpdateObjective:
    """Tests for PATCH /api/objectives/{id}."""

    def test_update_objective_title(self, authenticated_client):
        """Update changes title."""
        # Create objective
        create_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Original", "description": "Desc"}
        )
        obj_id = create_resp.json()["id"]

        response = authenticated_client.patch(
            f"/api/objectives/{obj_id}",
            json={"title": "Updated"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_update_retired_objective_fails(self, authenticated_client):
        """Cannot update retired objective."""
        # Create and retire
        create_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test", "description": "Desc"}
        )
        obj_id = create_resp.json()["id"]
        authenticated_client.post(f"/api/objectives/{obj_id}/retire")

        response = authenticated_client.patch(
            f"/api/objectives/{obj_id}",
            json={"title": "New Title"}
        )
        assert response.status_code == 400


class TestRetireObjective:
    """Tests for POST /api/objectives/{id}/retire."""

    def test_retire_objective_success(self, authenticated_client):
        """Retire changes status to Retired."""
        # Create objective
        create_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test", "description": "Desc"}
        )
        obj_id = create_resp.json()["id"]

        response = authenticated_client.post(f"/api/objectives/{obj_id}/retire")
        assert response.status_code == 200
        assert response.json()["status"] == "Retired"

    def test_retire_already_retired_fails(self, authenticated_client):
        """Cannot retire already retired objective."""
        # Create and retire
        create_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test", "description": "Desc"}
        )
        obj_id = create_resp.json()["id"]
        authenticated_client.post(f"/api/objectives/{obj_id}/retire")

        response = authenticated_client.post(f"/api/objectives/{obj_id}/retire")
        assert response.status_code == 400


class TestObjectiveWatching:
    """Tests for watching objectives."""

    def test_watch_objective(self, authenticated_client):
        """User can watch an objective."""
        # Create objective
        create_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test", "description": "Desc"}
        )
        obj_id = create_resp.json()["id"]

        response = authenticated_client.post(f"/api/objectives/{obj_id}/watch")
        assert response.status_code == 201
        assert response.json()["target_type"] == "objective"
        assert response.json()["target_id"] == obj_id

        # Verify is_watched in detail
        detail = authenticated_client.get(f"/api/objectives/{obj_id}")
        assert detail.json()["is_watched"] is True

    def test_unwatch_objective(self, authenticated_client):
        """User can unwatch an objective."""
        # Create and watch
        create_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test", "description": "Desc"}
        )
        obj_id = create_resp.json()["id"]
        authenticated_client.post(f"/api/objectives/{obj_id}/watch")

        response = authenticated_client.delete(f"/api/objectives/{obj_id}/watch")
        assert response.status_code == 204

        # Verify is_watched is False
        detail = authenticated_client.get(f"/api/objectives/{obj_id}")
        assert detail.json()["is_watched"] is False


class TestIdeaLinking:
    """Tests for linking ideas to objectives."""

    def test_link_idea_to_objective(self, authenticated_client, created_idea):
        """Can link an idea to an objective."""
        # Create objective
        obj_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test Obj", "description": "Desc"}
        )
        obj_id = obj_resp.json()["id"]

        response = authenticated_client.post(
            f"/api/objectives/{obj_id}/ideas",
            json={"idea_id": created_idea}
        )
        assert response.status_code == 201
        assert response.json()["idea_id"] == created_idea

    def test_list_linked_ideas(self, authenticated_client, created_idea):
        """Can list ideas linked to objective."""
        # Create objective and link
        obj_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test Obj", "description": "Desc"}
        )
        obj_id = obj_resp.json()["id"]
        authenticated_client.post(
            f"/api/objectives/{obj_id}/ideas",
            json={"idea_id": created_idea}
        )

        response = authenticated_client.get(f"/api/objectives/{obj_id}/ideas")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["idea_id"] == created_idea

    def test_unlink_idea_from_objective(self, authenticated_client, created_idea):
        """Can unlink an idea from objective."""
        # Create objective and link
        obj_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test Obj", "description": "Desc"}
        )
        obj_id = obj_resp.json()["id"]
        authenticated_client.post(
            f"/api/objectives/{obj_id}/ideas",
            json={"idea_id": created_idea}
        )

        response = authenticated_client.delete(
            f"/api/objectives/{obj_id}/ideas/{created_idea}"
        )
        assert response.status_code == 204

        # Verify unlinked
        ideas = authenticated_client.get(f"/api/objectives/{obj_id}/ideas")
        assert len(ideas.json()) == 0

    def test_cannot_link_to_retired_objective(self, authenticated_client, created_idea):
        """Cannot link ideas to retired objectives."""
        # Create and retire objective
        obj_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Test Obj", "description": "Desc"}
        )
        obj_id = obj_resp.json()["id"]
        authenticated_client.post(f"/api/objectives/{obj_id}/retire")

        response = authenticated_client.post(
            f"/api/objectives/{obj_id}/ideas",
            json={"idea_id": created_idea}
        )
        assert response.status_code == 400


class TestSubObjectives:
    """Tests for sub-objective endpoints."""

    def test_get_sub_objectives(self, authenticated_client):
        """Can get child objectives."""
        # Create parent
        parent_resp = authenticated_client.post(
            "/api/objectives",
            json={"title": "Parent", "description": "Parent desc"}
        )
        parent_id = parent_resp.json()["id"]

        # Create children
        for i in range(2):
            authenticated_client.post(
                "/api/objectives",
                json={
                    "title": f"Child {i}",
                    "description": f"Child {i} desc",
                    "parent_id": parent_id,
                }
            )

        response = authenticated_client.get(f"/api/objectives/{parent_id}/sub-objectives")
        assert response.status_code == 200
        assert len(response.json()) == 2
