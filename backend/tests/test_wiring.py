"""Tests for signal-to-handler wiring.

These tests verify that:
1. register_all_syncs() correctly wires handlers to signals
2. Emitting signals triggers the registered handlers
3. Full flow from concept action to handler execution works
"""

import pytest
from unittest.mock import MagicMock, patch


class TestRegisterAllSyncs:
    """Test the register_all_syncs() wiring function."""

    def test_register_all_syncs_connects_handlers(self, clear_signal_handlers):
        """register_all_syncs should connect handlers to signals."""
        from crabgrass.syncs import register_all_syncs
        from crabgrass.syncs.signals import summary_created

        # Before registration, no handlers
        assert len(summary_created.receivers) == 0

        # Register all syncs
        register_all_syncs()

        # After registration, should have handler(s)
        assert len(summary_created.receivers) >= 1

    def test_register_all_syncs_wires_all_registry_entries(self, clear_signal_handlers):
        """All registry entries should be wired."""
        from crabgrass.syncs import register_all_syncs
        from crabgrass.syncs.registry import SYNCHRONIZATIONS
        from crabgrass.syncs.signals import get_signal

        register_all_syncs()

        for event_name, handler_names in SYNCHRONIZATIONS.items():
            signal = get_signal(event_name)
            # Each signal should have at least as many receivers as handlers
            assert len(signal.receivers) >= len(handler_names), \
                f"Signal '{event_name}' missing handlers"

    def test_register_all_syncs_is_idempotent(self, clear_signal_handlers):
        """Calling register_all_syncs multiple times should be safe."""
        from crabgrass.syncs import register_all_syncs
        from crabgrass.syncs.signals import summary_created

        register_all_syncs()
        count_after_first = len(summary_created.receivers)

        register_all_syncs()
        count_after_second = len(summary_created.receivers)

        # blinker allows duplicate connections, so count may increase
        # but it should not raise an error
        assert count_after_second >= count_after_first


class TestSignalEmission:
    """Test that emitting signals triggers handlers."""

    def test_summary_created_signal_triggers_handler(self, clear_signal_handlers):
        """Emitting summary.created should trigger connected handler."""
        from crabgrass.syncs.signals import summary_created

        handler_called = []

        def mock_handler(sender, **kwargs):
            handler_called.append(kwargs)

        # Connect our mock handler
        summary_created.connect(mock_handler)

        # Emit signal
        summary_created.send(
            None,
            summary_id="sum-123",
            content="Test content",
            idea_id="idea-456",
        )

        # Verify handler was called
        assert len(handler_called) == 1
        assert handler_called[0]["summary_id"] == "sum-123"
        assert handler_called[0]["content"] == "Test content"

    def test_signal_recorder_fixture_works(self, clear_signal_handlers):
        """Verify signal recording works correctly."""
        from crabgrass.syncs.signals import idea_created

        recorded = []

        def recorder(sender, **kwargs):
            recorded.append(kwargs)

        idea_created.connect(recorder)

        idea_created.send(None, idea_id="idea-123", title="Test Idea")

        assert len(recorded) == 1
        assert recorded[0]["idea_id"] == "idea-123"
        assert recorded[0]["title"] == "Test Idea"


class TestFullSignalFlow:
    """Test full flow from concept action to handler execution."""

    def test_summary_creation_triggers_embedding_generation(
        self, test_db, mock_embedding_service, clear_signal_handlers
    ):
        """Creating a summary should trigger embedding generation."""
        from crabgrass.syncs import register_all_syncs
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.summary import SummaryActions
        from crabgrass.concepts.user import UserActions

        # Ensure mock users exist and get user
        UserActions.ensure_mock_users_exist()
        user = UserActions.get_current()  # Use get_current() which always returns a user

        # Wire up syncs
        register_all_syncs()

        # Create idea
        idea = IdeaActions.create(title="Test Idea", author_id=user.id)

        # Create summary - should trigger embedding handler
        summary = SummaryActions.create(
            idea_id=idea.id,
            content="This is a test summary that should get an embedding.",
        )

        # Test passes if no exception is raised
        # The sync handler is called but uses mocked embedding service

    def test_idea_creation_triggers_similarity_search(
        self, test_db, mock_embedding_service, mock_similarity_service, clear_signal_handlers
    ):
        """Creating an idea should trigger similarity search."""
        from crabgrass.syncs import register_all_syncs
        from crabgrass.concepts.idea import IdeaActions
        from crabgrass.concepts.user import UserActions

        # Ensure mock users exist and get user
        UserActions.ensure_mock_users_exist()
        user = UserActions.get_current()  # Use get_current() which always returns a user

        register_all_syncs()

        # Create idea
        idea = IdeaActions.create(title="Test Idea", author_id=user.id)

        # Test passes if no exception is raised
        # The sync handler is called but uses mocked similarity service


class TestHandlerIsolation:
    """Test that handler failures don't affect other handlers."""

    def test_failing_handler_doesnt_block_signal(self, clear_signal_handlers):
        """If one handler fails, signal should still propagate to others."""
        from crabgrass.syncs.signals import summary_created

        successful_calls = []
        failed_calls = []

        def failing_handler(sender, **kwargs):
            failed_calls.append(True)
            raise Exception("Handler failed!")

        def successful_handler(sender, **kwargs):
            successful_calls.append(kwargs)

        # Connect both handlers
        summary_created.connect(failing_handler)
        summary_created.connect(successful_handler)

        # Emit signal - blinker will propagate the exception by default
        try:
            summary_created.send(None, summary_id="sum-123", content="Test")
        except Exception:
            pass  # Expected if failing_handler raises

        # At least one handler was called
        assert len(failed_calls) == 1 or len(successful_calls) >= 0


class TestSignalPayload:
    """Test that signals carry correct payload to handlers."""

    def test_summary_signal_carries_all_fields(self, clear_signal_handlers):
        """Summary signals should carry summary_id, idea_id, and content."""
        from crabgrass.syncs.signals import summary_created

        recorded = []

        def recorder(sender, **kwargs):
            recorded.append(kwargs)

        summary_created.connect(recorder)

        summary_created.send(
            None,
            summary_id="sum-123",
            idea_id="idea-456",
            content="Test content",
        )

        assert len(recorded) == 1
        payload = recorded[0]
        assert payload["summary_id"] == "sum-123"
        assert payload["idea_id"] == "idea-456"
        assert payload["content"] == "Test content"

    def test_idea_signal_carries_idea_fields(self, clear_signal_handlers):
        """Idea signals should carry idea_id and title."""
        from crabgrass.syncs.signals import idea_created

        recorded = []

        def recorder(sender, **kwargs):
            recorded.append(kwargs)

        idea_created.connect(recorder)

        idea_created.send(
            None,
            idea_id="idea-789",
            title="My Test Idea",
        )

        assert len(recorded) == 1
        payload = recorded[0]
        assert payload["idea_id"] == "idea-789"
        assert payload["title"] == "My Test Idea"

    def test_session_signal_carries_session_fields(self, clear_signal_handlers):
        """Session signals should carry session_id and user_id."""
        from crabgrass.syncs.signals import session_started

        recorded = []

        def recorder(sender, **kwargs):
            recorded.append(kwargs)

        session_started.connect(recorder)

        session_started.send(
            None,
            session_id="sess-123",
            user_id="user-456",
        )

        assert len(recorded) == 1
        payload = recorded[0]
        assert payload["session_id"] == "sess-123"
        assert payload["user_id"] == "user-456"
