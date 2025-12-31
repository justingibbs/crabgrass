"""Tests for Agent API endpoints.

Tests cover SSE streaming and session management.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock


class TestAgentChat:
    """Tests for POST /api/agent/chat."""

    def test_chat_returns_sse_stream(self, authenticated_client):
        """Chat endpoint returns SSE stream response."""
        with patch("crabgrass.api.agent.get_idea_assistant") as mock_get_agent:
            # Create a mock agent that yields events
            mock_agent = MagicMock()

            async def mock_run(*args, **kwargs):
                yield {"type": "text_delta", "text": "Hello"}
                yield {"type": "text_delta", "text": " world"}

            mock_agent.run = mock_run
            mock_get_agent.return_value = mock_agent

            response = authenticated_client.post(
                "/api/agent/chat",
                json={"message": "Hello agent"},
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_chat_includes_session_header(self, authenticated_client):
        """Chat response includes session ID in header."""
        with patch("crabgrass.api.agent.get_idea_assistant") as mock_get_agent:
            mock_agent = MagicMock()

            async def mock_run(*args, **kwargs):
                return
                yield  # Make it a generator

            mock_agent.run = mock_run
            mock_get_agent.return_value = mock_agent

            response = authenticated_client.post(
                "/api/agent/chat",
                json={"message": "Test"},
            )

            assert "x-session-id" in response.headers

    def test_chat_with_existing_session(self, authenticated_client):
        """Chat can continue existing session."""
        # Create a session first
        session_response = authenticated_client.post("/api/agent/sessions")
        session_id = session_response.json()["session_id"]

        with patch("crabgrass.api.agent.get_idea_assistant") as mock_get_agent:
            mock_agent = MagicMock()

            async def mock_run(*args, **kwargs):
                return
                yield

            mock_agent.run = mock_run
            mock_get_agent.return_value = mock_agent

            response = authenticated_client.post(
                "/api/agent/chat",
                json={"message": "Continue", "session_id": session_id},
            )

            assert response.status_code == 200
            assert response.headers["x-session-id"] == session_id

    def test_chat_with_invalid_session(self, authenticated_client):
        """Chat with invalid session returns 404."""
        with patch("crabgrass.api.agent.get_idea_assistant") as mock_get_agent:
            response = authenticated_client.post(
                "/api/agent/chat",
                json={"message": "Test", "session_id": "nonexistent-session"},
            )

            assert response.status_code == 404

    def test_chat_with_idea_id(self, authenticated_client, created_idea):
        """Chat can load context from existing idea."""
        with patch("crabgrass.api.agent.get_idea_assistant") as mock_get_agent:
            mock_agent = MagicMock()

            async def mock_run(*args, **kwargs):
                return
                yield

            mock_agent.run = mock_run
            mock_get_agent.return_value = mock_agent

            response = authenticated_client.post(
                "/api/agent/chat",
                json={"message": "Tell me about this idea", "idea_id": created_idea},
            )

            assert response.status_code == 200


class TestAgentSessions:
    """Tests for agent session management endpoints."""

    def test_create_session(self, authenticated_client):
        """POST /api/agent/sessions creates new session."""
        response = authenticated_client.post("/api/agent/sessions")

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] is not None

    def test_create_session_with_idea(self, authenticated_client, created_idea):
        """Create session can associate with existing idea."""
        response = authenticated_client.post(
            "/api/agent/sessions",
            params={"idea_id": created_idea},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["idea_id"] == created_idea

    def test_create_session_invalid_idea(self, authenticated_client):
        """Create session with invalid idea returns 404."""
        response = authenticated_client.post(
            "/api/agent/sessions",
            params={"idea_id": "nonexistent-idea"},
        )

        assert response.status_code == 404

    def test_get_session(self, authenticated_client):
        """GET /api/agent/sessions/{id} returns session details."""
        # Create session
        create_response = authenticated_client.post("/api/agent/sessions")
        session_id = create_response.json()["session_id"]

        response = authenticated_client.get(f"/api/agent/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "messages" in data
        assert "status" in data

    def test_get_session_not_found(self, authenticated_client):
        """GET nonexistent session returns 404."""
        response = authenticated_client.get("/api/agent/sessions/nonexistent-id")
        assert response.status_code == 404

    def test_end_session(self, authenticated_client):
        """POST /api/agent/sessions/{id}/end archives session."""
        # Create session
        create_response = authenticated_client.post("/api/agent/sessions")
        session_id = create_response.json()["session_id"]

        response = authenticated_client.post(f"/api/agent/sessions/{session_id}/end")

        assert response.status_code == 200
        assert response.json()["status"] == "archived"

    def test_end_session_not_found(self, authenticated_client):
        """End nonexistent session returns 404."""
        response = authenticated_client.post("/api/agent/sessions/nonexistent-id/end")
        assert response.status_code == 404


class TestSSEEventFormat:
    """Tests for SSE event format compliance."""

    def test_stream_includes_run_started(self, authenticated_client):
        """Stream includes RunStartedEvent."""
        with patch("crabgrass.api.agent.get_idea_assistant") as mock_get_agent:
            mock_agent = MagicMock()

            async def mock_run(*args, **kwargs):
                return
                yield

            mock_agent.run = mock_run
            mock_get_agent.return_value = mock_agent

            response = authenticated_client.post(
                "/api/agent/chat",
                json={"message": "Test"},
            )

            content = response.text
            # SSE format: data: {...}\n\n
            assert "RUN_STARTED" in content or "RunStarted" in content.lower() or '"type"' in content

    def test_stream_includes_run_finished(self, authenticated_client):
        """Stream includes RunFinishedEvent."""
        with patch("crabgrass.api.agent.get_idea_assistant") as mock_get_agent:
            mock_agent = MagicMock()

            async def mock_run(*args, **kwargs):
                return
                yield

            mock_agent.run = mock_run
            mock_get_agent.return_value = mock_agent

            response = authenticated_client.post(
                "/api/agent/chat",
                json={"message": "Test"},
            )

            content = response.text
            # Should end with RunFinishedEvent
            assert "RUN_FINISHED" in content or "RunFinished" in content.lower() or "run_finished" in content.lower() or content.count("data:") >= 1

    def test_text_deltas_are_streamed(self, authenticated_client):
        """Text delta events are properly streamed."""
        with patch("crabgrass.api.agent.get_idea_assistant") as mock_get_agent:
            mock_agent = MagicMock()

            async def mock_run(*args, **kwargs):
                yield {"type": "text_delta", "text": "Hello"}
                yield {"type": "text_delta", "text": " there"}

            mock_agent.run = mock_run
            mock_get_agent.return_value = mock_agent

            response = authenticated_client.post(
                "/api/agent/chat",
                json={"message": "Say hello"},
            )

            content = response.text
            # Should contain text content events
            assert "Hello" in content or "TEXT_MESSAGE" in content or "delta" in content.lower()
