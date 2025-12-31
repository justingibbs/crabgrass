"""API test fixtures.

Provides TestClient and auth headers for API testing.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def api_client(test_db, mock_embedding_service):
    """Create a FastAPI test client with initialized database.

    Patches embedding service to avoid real API calls.
    """
    from crabgrass.main import create_app

    app = create_app()

    with TestClient(app) as client:
        yield client


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Client with authenticated user context.

    The test_user fixture ensures mock users are created.
    """
    return api_client


@pytest.fixture
def created_idea(authenticated_client):
    """Create a test idea via API and return its ID.

    Useful for tests that need an existing idea.
    """
    response = authenticated_client.post(
        "/api/ideas",
        json={
            "title": "Test Idea via API",
            "summary": {"content": "This is a test summary created via API."},
        },
    )
    assert response.status_code == 200
    data = response.json()
    return data["id"]
