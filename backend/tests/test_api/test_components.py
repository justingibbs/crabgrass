"""Tests for Idea Component API endpoints.

Tests cover Summary, Challenge, Approach, and CoherentAction endpoints.
"""

import pytest


class TestSummaryEndpoints:
    """Tests for /api/ideas/{idea_id}/summary endpoints."""

    def test_create_summary_success(self, authenticated_client, created_idea):
        """Creating summary when one already exists fails (created with idea)."""
        # Note: created_idea already has a summary
        response = authenticated_client.post(
            f"/api/ideas/{created_idea}/summary",
            json={"content": "Another summary"},
        )
        # Should fail because summary already exists
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_summary_success(self, authenticated_client, created_idea):
        """Update summary changes content."""
        response = authenticated_client.patch(
            f"/api/ideas/{created_idea}/summary",
            json={"content": "Updated summary content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated summary content"

    def test_update_summary_not_found(self, authenticated_client):
        """Update summary returns 404 for nonexistent idea."""
        response = authenticated_client.patch(
            "/api/ideas/nonexistent-id/summary",
            json={"content": "Test"},
        )
        assert response.status_code == 404


class TestChallengeEndpoints:
    """Tests for /api/ideas/{idea_id}/challenge endpoints."""

    def test_create_challenge_success(self, authenticated_client, created_idea):
        """Create challenge returns challenge response."""
        response = authenticated_client.post(
            f"/api/ideas/{created_idea}/challenge",
            json={"content": "What is the main challenge?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "What is the main challenge?"
        assert data["id"] is not None

    def test_create_challenge_duplicate(self, authenticated_client, created_idea):
        """Creating challenge when one exists fails."""
        # Create first challenge
        authenticated_client.post(
            f"/api/ideas/{created_idea}/challenge",
            json={"content": "First challenge"},
        )

        # Try to create another
        response = authenticated_client.post(
            f"/api/ideas/{created_idea}/challenge",
            json={"content": "Second challenge"},
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_challenge_success(self, authenticated_client, created_idea):
        """Update challenge changes content."""
        # Create challenge first
        authenticated_client.post(
            f"/api/ideas/{created_idea}/challenge",
            json={"content": "Original challenge"},
        )

        response = authenticated_client.patch(
            f"/api/ideas/{created_idea}/challenge",
            json={"content": "Updated challenge"},
        )

        assert response.status_code == 200
        assert response.json()["content"] == "Updated challenge"

    def test_delete_challenge_success(self, authenticated_client, created_idea):
        """Delete challenge removes it."""
        # Create challenge first
        authenticated_client.post(
            f"/api/ideas/{created_idea}/challenge",
            json={"content": "To be deleted"},
        )

        response = authenticated_client.delete(f"/api/ideas/{created_idea}/challenge")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_challenge_not_found(self, authenticated_client, created_idea):
        """Delete returns 404 when no challenge exists."""
        response = authenticated_client.delete(f"/api/ideas/{created_idea}/challenge")
        assert response.status_code == 404


class TestApproachEndpoints:
    """Tests for /api/ideas/{idea_id}/approach endpoints."""

    def test_create_approach_success(self, authenticated_client, created_idea):
        """Create approach returns approach response."""
        response = authenticated_client.post(
            f"/api/ideas/{created_idea}/approach",
            json={"content": "How we will solve this"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "How we will solve this"
        assert data["id"] is not None

    def test_create_approach_duplicate(self, authenticated_client, created_idea):
        """Creating approach when one exists fails."""
        # Create first approach
        authenticated_client.post(
            f"/api/ideas/{created_idea}/approach",
            json={"content": "First approach"},
        )

        # Try to create another
        response = authenticated_client.post(
            f"/api/ideas/{created_idea}/approach",
            json={"content": "Second approach"},
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_approach_success(self, authenticated_client, created_idea):
        """Update approach changes content."""
        # Create approach first
        authenticated_client.post(
            f"/api/ideas/{created_idea}/approach",
            json={"content": "Original approach"},
        )

        response = authenticated_client.patch(
            f"/api/ideas/{created_idea}/approach",
            json={"content": "Updated approach"},
        )

        assert response.status_code == 200
        assert response.json()["content"] == "Updated approach"

    def test_delete_approach_success(self, authenticated_client, created_idea):
        """Delete approach removes it."""
        # Create approach first
        authenticated_client.post(
            f"/api/ideas/{created_idea}/approach",
            json={"content": "To be deleted"},
        )

        response = authenticated_client.delete(f"/api/ideas/{created_idea}/approach")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"


class TestCoherentActionEndpoints:
    """Tests for /api/ideas/{idea_id}/actions endpoints."""

    def test_list_actions_empty(self, authenticated_client, created_idea):
        """List actions returns empty array initially."""
        response = authenticated_client.get(f"/api/ideas/{created_idea}/actions")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_action_success(self, authenticated_client, created_idea):
        """Create action returns action response."""
        response = authenticated_client.post(
            f"/api/ideas/{created_idea}/actions",
            json={"content": "First action step"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "First action step"
        assert data["status"] == "Pending"

    def test_list_actions_returns_created(self, authenticated_client, created_idea):
        """List returns created actions."""
        # Create some actions
        authenticated_client.post(
            f"/api/ideas/{created_idea}/actions",
            json={"content": "Action 1"},
        )
        authenticated_client.post(
            f"/api/ideas/{created_idea}/actions",
            json={"content": "Action 2"},
        )

        response = authenticated_client.get(f"/api/ideas/{created_idea}/actions")
        actions = response.json()
        assert len(actions) == 2

    def test_update_action_content(self, authenticated_client, created_idea):
        """Update action changes content."""
        # Create action
        create_response = authenticated_client.post(
            f"/api/ideas/{created_idea}/actions",
            json={"content": "Original content"},
        )
        action_id = create_response.json()["id"]

        response = authenticated_client.patch(
            f"/api/ideas/{created_idea}/actions/{action_id}",
            json={"content": "Updated content"},
        )

        assert response.status_code == 200
        assert response.json()["content"] == "Updated content"

    def test_complete_action(self, authenticated_client, created_idea):
        """Complete action changes status."""
        # Create action
        create_response = authenticated_client.post(
            f"/api/ideas/{created_idea}/actions",
            json={"content": "Task to complete"},
        )
        action_id = create_response.json()["id"]

        response = authenticated_client.post(
            f"/api/ideas/{created_idea}/actions/{action_id}/complete"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "Complete"

    def test_delete_action_success(self, authenticated_client, created_idea):
        """Delete action removes it."""
        # Create action
        create_response = authenticated_client.post(
            f"/api/ideas/{created_idea}/actions",
            json={"content": "To be deleted"},
        )
        action_id = create_response.json()["id"]

        response = authenticated_client.delete(
            f"/api/ideas/{created_idea}/actions/{action_id}"
        )
        assert response.status_code == 200

        # Verify it's gone
        list_response = authenticated_client.get(f"/api/ideas/{created_idea}/actions")
        actions = list_response.json()
        assert not any(a["id"] == action_id for a in actions)

    def test_action_wrong_idea_not_found(self, authenticated_client, created_idea):
        """Action operations return 404 if action belongs to different idea."""
        # Create action
        create_response = authenticated_client.post(
            f"/api/ideas/{created_idea}/actions",
            json={"content": "Test action"},
        )
        action_id = create_response.json()["id"]

        # Try to access with wrong idea
        response = authenticated_client.patch(
            f"/api/ideas/wrong-idea-id/actions/{action_id}",
            json={"content": "Updated"},
        )
        assert response.status_code == 404
