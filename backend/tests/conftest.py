"""Shared test fixtures for Crabgrass backend tests.

Provides fixtures for:
- Mock embedding service (avoids Gemini API calls)
- Test database isolation
- Test user and idea creation
- Signal recording for verification
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Set test environment before imports
os.environ["GOOGLE_API_KEY"] = "test-api-key"
os.environ["DATABASE_PATH"] = ":memory:"


# ─────────────────────────────────────────────────────────────────────────────
# Database Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def test_db():
    """Provide a fresh in-memory database for each test.

    Initializes schema and cleans up after test.
    """
    from crabgrass.database import init_schema, close_connection

    # Initialize fresh schema
    init_schema()

    yield

    # Cleanup
    close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# Mock Service Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service to avoid Gemini API calls.

    Returns a consistent 768-dimension embedding vector.
    """
    mock_embedding = [0.1] * 768

    with patch("crabgrass.services.embedding.EmbeddingService") as MockClass:
        mock_instance = MagicMock()
        mock_instance.embed.return_value = mock_embedding
        mock_instance.embed_batch.return_value = [mock_embedding]
        MockClass.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_similarity_service():
    """Mock similarity service for testing without real embeddings."""
    with patch("crabgrass.services.similarity.SimilarityService") as MockClass:
        mock_instance = MagicMock()
        # Return empty by default, tests can configure as needed
        mock_instance.find_similar_for_idea.return_value = []
        mock_instance.find_similar_summaries.return_value = []
        MockClass.return_value = mock_instance
        yield mock_instance


# ─────────────────────────────────────────────────────────────────────────────
# Test Data Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def test_user(test_db):
    """Create a test user for authenticated operations."""
    from crabgrass.concepts.user import UserActions

    # Ensure mock users exist (includes Sarah and others)
    UserActions.ensure_mock_users_exist()

    # Return Sarah as the test user
    user = UserActions.get_by_id("sarah-001")
    return user


@pytest.fixture
def test_idea(test_db, test_user, mock_embedding_service):
    """Create a test idea with all components.

    Returns an idea with:
    - Summary
    - Challenge
    - Approach
    - 2 coherent actions
    """
    from crabgrass.concepts.idea import IdeaActions
    from crabgrass.concepts.summary import SummaryActions
    from crabgrass.concepts.challenge import ChallengeActions
    from crabgrass.concepts.approach import ApproachActions
    from crabgrass.concepts.coherent_action import CoherentActionActions

    # Create idea
    idea = IdeaActions.create(
        title="Test Idea for Unit Tests",
        author_id=test_user.id,
    )

    # Create summary
    SummaryActions.create(
        idea_id=idea.id,
        content="This is a test summary for automated testing.",
    )

    # Create challenge
    ChallengeActions.create(
        idea_id=idea.id,
        content="The challenge is to validate our sync system works correctly.",
    )

    # Create approach
    ApproachActions.create(
        idea_id=idea.id,
        content="We will use pytest with mocks to isolate tests.",
    )

    # Create actions
    CoherentActionActions.create(
        idea_id=idea.id,
        content="Write unit tests for handlers",
    )
    CoherentActionActions.create(
        idea_id=idea.id,
        content="Write integration tests for full flow",
    )

    return idea


@pytest.fixture
def minimal_idea(test_db, test_user, mock_embedding_service):
    """Create a minimal idea with just a title (no summary)."""
    from crabgrass.concepts.idea import IdeaActions

    idea = IdeaActions.create(
        title="Minimal Test Idea",
        author_id=test_user.id,
    )
    return idea


# ─────────────────────────────────────────────────────────────────────────────
# Signal Recording Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def signal_recorder():
    """Records signals emitted during a test.

    Usage:
        recorded, connect = signal_recorder
        from crabgrass.syncs.signals import summary_created
        summary_created.connect(connect("summary.created"))

        # ... do something that emits signal ...

        assert len(recorded) == 1
        assert recorded[0]["signal"] == "summary.created"
    """
    recorded = []

    def create_recorder(signal_name: str):
        """Create a recorder function for a specific signal."""
        def handler(sender, **kwargs):
            recorded.append({
                "signal": signal_name,
                "sender": sender,
                "timestamp": datetime.utcnow(),
                **kwargs,
            })
        return handler

    return recorded, create_recorder


@pytest.fixture
def clear_signal_handlers():
    """Clear all signal handlers before and after a test.

    Useful for testing signal wiring in isolation.
    Note: This fixture only clears handlers, it doesn't restore them.
    This is intentional to keep tests isolated.
    """
    from crabgrass.syncs.signals import sync_signals

    # Clear all signal receivers before test
    for name in sync_signals:
        signal = sync_signals.signal(name)
        signal.receivers.clear()

    yield

    # Clear again after test to ensure clean state
    for name in sync_signals:
        signal = sync_signals.signal(name)
        signal.receivers.clear()


# ─────────────────────────────────────────────────────────────────────────────
# API Test Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def app():
    """Create a FastAPI test app instance."""
    from crabgrass.main import create_app
    return create_app()


@pytest.fixture
def client(app, test_db):
    """Create a FastAPI test client.

    Includes database initialization.
    """
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def auth_headers(test_user):
    """Headers for authenticated API requests.

    Currently returns minimal headers since auth is mocked.
    """
    return {
        "Content-Type": "application/json",
    }
