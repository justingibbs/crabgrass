"""Tests for sync handlers.

These tests verify handler behavior in isolation using mocks.
Handlers should:
1. Call the appropriate services
2. Update the database correctly
3. Handle errors gracefully
"""

import pytest
from unittest.mock import MagicMock, patch, call


class TestEmbeddingHandlers:
    """Test embedding generation handlers."""

    def test_generate_summary_embedding_calls_service(self):
        """Handler should call EmbeddingService.embed with content."""
        mock_service = MagicMock()
        mock_service.embed.return_value = [0.1] * 768

        mock_summary_actions = MagicMock()

        with patch.dict("sys.modules", {
            "crabgrass.services.embedding": MagicMock(EmbeddingService=lambda: mock_service),
            "crabgrass.concepts.summary": MagicMock(SummaryActions=mock_summary_actions),
        }):
            # Re-import to pick up the mocks
            from crabgrass.syncs.handlers.embedding import generate_summary_embedding

            generate_summary_embedding(
                sender=None,
                summary_id="sum-123",
                content="Test summary content",
            )

            # Verify embed was called with the content
            mock_service.embed.assert_called_once_with("Test summary content")

    def test_generate_summary_embedding_updates_database(self):
        """Handler should call SummaryActions.update_embedding."""
        test_embedding = [0.1] * 768

        mock_service = MagicMock()
        mock_service.embed.return_value = test_embedding

        mock_summary_actions = MagicMock()

        with patch.dict("sys.modules", {
            "crabgrass.services.embedding": MagicMock(EmbeddingService=lambda: mock_service),
            "crabgrass.concepts.summary": MagicMock(SummaryActions=mock_summary_actions),
        }):
            from crabgrass.syncs.handlers.embedding import generate_summary_embedding

            generate_summary_embedding(
                sender=None,
                summary_id="sum-123",
                content="Test content",
            )

            mock_summary_actions.update_embedding.assert_called_once_with("sum-123", test_embedding)

    def test_generate_summary_embedding_handles_service_error(self, caplog):
        """Handler should log error if embedding service fails."""
        mock_service = MagicMock()
        mock_service.embed.side_effect = Exception("API Error")

        with patch.dict("sys.modules", {
            "crabgrass.services.embedding": MagicMock(EmbeddingService=lambda: mock_service),
        }):
            from crabgrass.syncs.handlers.embedding import generate_summary_embedding

            # Should not raise
            generate_summary_embedding(
                sender=None,
                summary_id="sum-123",
                content="Test content",
            )

            # No exception raised - handler catches it

    def test_generate_challenge_embedding_calls_service(self):
        """Challenge embedding handler should call EmbeddingService."""
        mock_service = MagicMock()
        mock_service.embed.return_value = [0.2] * 768

        mock_challenge_actions = MagicMock()

        with patch.dict("sys.modules", {
            "crabgrass.services.embedding": MagicMock(EmbeddingService=lambda: mock_service),
            "crabgrass.concepts.challenge": MagicMock(ChallengeActions=mock_challenge_actions),
        }):
            from crabgrass.syncs.handlers.embedding import generate_challenge_embedding

            generate_challenge_embedding(
                sender=None,
                challenge_id="chal-123",
                content="Test challenge content",
            )

            mock_service.embed.assert_called_once_with("Test challenge content")
            mock_challenge_actions.update_embedding.assert_called_once()

    def test_generate_approach_embedding_calls_service(self):
        """Approach embedding handler should call EmbeddingService."""
        mock_service = MagicMock()
        mock_service.embed.return_value = [0.3] * 768

        mock_approach_actions = MagicMock()

        with patch.dict("sys.modules", {
            "crabgrass.services.embedding": MagicMock(EmbeddingService=lambda: mock_service),
            "crabgrass.concepts.approach": MagicMock(ApproachActions=mock_approach_actions),
        }):
            from crabgrass.syncs.handlers.embedding import generate_approach_embedding

            generate_approach_embedding(
                sender=None,
                approach_id="app-123",
                content="Test approach content",
            )

            mock_service.embed.assert_called_once_with("Test approach content")
            mock_approach_actions.update_embedding.assert_called_once()


class TestSimilarityHandlers:
    """Test similarity search handlers."""

    def test_find_similar_ideas_calls_service(self):
        """Handler should call SimilarityService.find_similar_for_idea."""
        mock_service = MagicMock()
        mock_service.find_similar_for_idea.return_value = []

        with patch.dict("sys.modules", {
            "crabgrass.services.similarity": MagicMock(SimilarityService=lambda: mock_service),
        }):
            from crabgrass.syncs.handlers.similarity import find_similar_ideas

            find_similar_ideas(sender=None, idea_id="idea-123")

            mock_service.find_similar_for_idea.assert_called_once_with("idea-123")

    def test_find_similar_ideas_returns_results(self):
        """Handler should return list of similar ideas."""
        mock_results = [
            MagicMock(idea_id="idea-1", title="Similar 1", similarity=0.9),
            MagicMock(idea_id="idea-2", title="Similar 2", similarity=0.8),
        ]

        mock_service = MagicMock()
        mock_service.find_similar_for_idea.return_value = mock_results

        with patch.dict("sys.modules", {
            "crabgrass.services.similarity": MagicMock(SimilarityService=lambda: mock_service),
        }):
            from crabgrass.syncs.handlers.similarity import find_similar_ideas

            result = find_similar_ideas(sender=None, idea_id="idea-123")

            assert result == mock_results
            assert len(result) == 2

    def test_find_similar_ideas_returns_none_on_error(self):
        """Handler should return None if service fails."""
        mock_service = MagicMock()
        mock_service.find_similar_for_idea.side_effect = Exception("Error")

        with patch.dict("sys.modules", {
            "crabgrass.services.similarity": MagicMock(SimilarityService=lambda: mock_service),
        }):
            from crabgrass.syncs.handlers.similarity import find_similar_ideas

            result = find_similar_ideas(sender=None, idea_id="idea-123")

            assert result is None


class TestLoggingHandlers:
    """Test session logging handlers."""

    def test_log_session_start_logs_info(self, caplog):
        """Handler should log session start information."""
        import logging

        caplog.set_level(logging.INFO)

        from crabgrass.syncs.handlers.logging import log_session_start

        log_session_start(
            sender=None,
            session_id="sess-123",
            user_id="user-456",
        )

        # Handler should have logged something about the session
        assert any("session" in record.message.lower() for record in caplog.records)

    def test_log_session_start_with_idea(self, caplog):
        """Handler should log with idea_id when provided."""
        import logging

        caplog.set_level(logging.INFO)

        from crabgrass.syncs.handlers.logging import log_session_start

        log_session_start(
            sender=None,
            session_id="sess-123",
            user_id="user-456",
            idea_id="idea-789",
        )

        # Should include idea reference
        assert any("idea" in record.message.lower() for record in caplog.records)

    def test_log_session_end_logs_info(self, caplog):
        """Handler should log session end information."""
        import logging

        caplog.set_level(logging.INFO)

        from crabgrass.syncs.handlers.logging import log_session_end

        log_session_end(
            sender=None,
            session_id="sess-123",
            user_id="user-456",
        )

        # Should log session end
        assert any("session" in record.message.lower() for record in caplog.records)


class TestHandlerKwargsHandling:
    """Test that handlers correctly handle extra kwargs."""

    def test_embedding_handler_ignores_extra_kwargs(self):
        """Handlers should accept extra kwargs without error."""
        mock_service = MagicMock()
        mock_service.embed.return_value = [0.1] * 768

        mock_summary_actions = MagicMock()

        with patch.dict("sys.modules", {
            "crabgrass.services.embedding": MagicMock(EmbeddingService=lambda: mock_service),
            "crabgrass.concepts.summary": MagicMock(SummaryActions=mock_summary_actions),
        }):
            from crabgrass.syncs.handlers.embedding import generate_summary_embedding

            # Should not raise even with extra kwargs
            generate_summary_embedding(
                sender=None,
                summary_id="sum-123",
                content="Test content",
                idea_id="idea-456",  # Extra kwarg
                unknown_param="ignored",  # Another extra kwarg
            )

    def test_similarity_handler_ignores_extra_kwargs(self):
        """Similarity handler should accept extra kwargs."""
        mock_service = MagicMock()
        mock_service.find_similar_for_idea.return_value = []

        with patch.dict("sys.modules", {
            "crabgrass.services.similarity": MagicMock(SimilarityService=lambda: mock_service),
        }):
            from crabgrass.syncs.handlers.similarity import find_similar_ideas

            # Should not raise even with extra kwargs
            result = find_similar_ideas(
                sender=None,
                idea_id="idea-123",
                content="some content",  # Extra kwarg
                timestamp="2024-01-01",  # Another extra kwarg
            )

            assert result == []


class TestHandlerIdempotency:
    """Test that handlers are reasonably idempotent."""

    def test_embedding_handler_can_be_called_multiple_times(self):
        """Calling embedding handler multiple times should update embedding each time."""
        mock_service = MagicMock()
        mock_service.embed.return_value = [0.1] * 768

        mock_summary_actions = MagicMock()

        with patch.dict("sys.modules", {
            "crabgrass.services.embedding": MagicMock(EmbeddingService=lambda: mock_service),
            "crabgrass.concepts.summary": MagicMock(SummaryActions=mock_summary_actions),
        }):
            from crabgrass.syncs.handlers.embedding import generate_summary_embedding

            # Call twice
            generate_summary_embedding(sender=None, summary_id="sum-1", content="Content A")
            generate_summary_embedding(sender=None, summary_id="sum-1", content="Content B")

            # Should have called update_embedding twice
            assert mock_summary_actions.update_embedding.call_count == 2
