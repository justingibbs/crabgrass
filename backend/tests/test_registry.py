"""Tests for the synchronization registry.

These tests verify that:
1. Expected sync contracts are declared
2. All handler names resolve to actual functions
3. Handler signatures follow conventions
"""

import inspect
import pytest

from crabgrass.syncs.registry import SYNCHRONIZATIONS
from crabgrass.syncs.handlers import HANDLERS, get_handler
from crabgrass.syncs.signals import get_signal, sync_signals


class TestRegistryContracts:
    """Verify the registry declares expected contracts."""

    def test_registry_is_not_empty(self):
        """Registry should have at least some entries."""
        assert len(SYNCHRONIZATIONS) > 0

    def test_summary_created_triggers_embedding(self):
        """Contract: summary.created → generate_summary_embedding"""
        assert "summary.created" in SYNCHRONIZATIONS
        assert "generate_summary_embedding" in SYNCHRONIZATIONS["summary.created"]

    def test_summary_updated_triggers_embedding_and_connection_queue(self):
        """Contract: summary.updated → embedding + enqueue for async processing"""
        handlers = SYNCHRONIZATIONS["summary.updated"]
        assert "generate_summary_embedding" in handlers
        assert "enqueue_connection" in handlers

    def test_challenge_created_triggers_embedding(self):
        """Contract: challenge.created → generate_challenge_embedding"""
        assert "challenge.created" in SYNCHRONIZATIONS
        assert "generate_challenge_embedding" in SYNCHRONIZATIONS["challenge.created"]

    def test_challenge_updated_triggers_embedding(self):
        """Contract: challenge.updated → generate_challenge_embedding"""
        assert "challenge.updated" in SYNCHRONIZATIONS
        assert "generate_challenge_embedding" in SYNCHRONIZATIONS["challenge.updated"]

    def test_approach_created_triggers_embedding(self):
        """Contract: approach.created → generate_approach_embedding"""
        assert "approach.created" in SYNCHRONIZATIONS
        assert "generate_approach_embedding" in SYNCHRONIZATIONS["approach.created"]

    def test_approach_updated_triggers_embedding(self):
        """Contract: approach.updated → generate_approach_embedding"""
        assert "approach.updated" in SYNCHRONIZATIONS
        assert "generate_approach_embedding" in SYNCHRONIZATIONS["approach.updated"]

    def test_idea_created_triggers_connection_queue(self):
        """Contract: idea.created → enqueue_connection for async processing"""
        assert "idea.created" in SYNCHRONIZATIONS
        assert "enqueue_connection" in SYNCHRONIZATIONS["idea.created"]

    def test_session_started_triggers_logging(self):
        """Contract: session.started → log_session_start"""
        assert "session.started" in SYNCHRONIZATIONS
        assert "log_session_start" in SYNCHRONIZATIONS["session.started"]

    def test_session_ended_triggers_logging(self):
        """Contract: session.ended → log_session_end"""
        assert "session.ended" in SYNCHRONIZATIONS
        assert "log_session_end" in SYNCHRONIZATIONS["session.ended"]

    # V2 Contracts - Objectives
    def test_objective_created_triggers_surfacing(self):
        """Contract: objective.created → enqueue_surfacing_objective_created"""
        assert "objective.created" in SYNCHRONIZATIONS
        assert "enqueue_surfacing_objective_created" in SYNCHRONIZATIONS["objective.created"]

    def test_objective_updated_triggers_surfacing(self):
        """Contract: objective.updated → enqueue_surfacing_objective_updated"""
        assert "objective.updated" in SYNCHRONIZATIONS
        assert "enqueue_surfacing_objective_updated" in SYNCHRONIZATIONS["objective.updated"]

    def test_objective_retired_triggers_surfacing_and_review(self):
        """Contract: objective.retired → surfacing + objective review"""
        handlers = SYNCHRONIZATIONS["objective.retired"]
        assert "enqueue_surfacing_objective_retired" in handlers
        assert "enqueue_objective_review" in handlers

    # V2 Contracts - Idea Linking
    def test_idea_linked_triggers_surfacing(self):
        """Contract: idea.linked_to_objective → enqueue_surfacing_linked"""
        assert "idea.linked_to_objective" in SYNCHRONIZATIONS
        assert "enqueue_surfacing_linked" in SYNCHRONIZATIONS["idea.linked_to_objective"]

    def test_idea_structure_added_removes_from_nurture(self):
        """Contract: idea.structure_added → remove_from_nurture_queue"""
        assert "idea.structure_added" in SYNCHRONIZATIONS
        assert "remove_from_nurture_queue" in SYNCHRONIZATIONS["idea.structure_added"]

    # V2 Contracts - Agent Signals
    def test_agent_found_similarity_triggers_graph_and_surfacing(self):
        """Contract: agent.found_similarity → graph + surfacing"""
        handlers = SYNCHRONIZATIONS["agent.found_similarity"]
        assert "create_similarity_relationship" in handlers
        assert "enqueue_surfacing_similarity" in handlers

    def test_agent_found_relevant_user_triggers_graph_and_surfacing(self):
        """Contract: agent.found_relevant_user → graph + surfacing"""
        handlers = SYNCHRONIZATIONS["agent.found_relevant_user"]
        assert "create_interest_relationship" in handlers
        assert "enqueue_surfacing_interest" in handlers

    def test_agent_suggest_reconnection_triggers_surfacing(self):
        """Contract: agent.suggest_reconnection → enqueue_surfacing_reconnection"""
        assert "agent.suggest_reconnection" in SYNCHRONIZATIONS
        assert "enqueue_surfacing_reconnection" in SYNCHRONIZATIONS["agent.suggest_reconnection"]

    def test_agent_flag_orphan_triggers_surfacing(self):
        """Contract: agent.flag_orphan → enqueue_surfacing_orphan"""
        assert "agent.flag_orphan" in SYNCHRONIZATIONS
        assert "enqueue_surfacing_orphan" in SYNCHRONIZATIONS["agent.flag_orphan"]


class TestHandlerResolution:
    """Verify all handler names in registry resolve to functions."""

    def test_all_handlers_exist(self):
        """Every handler name in registry must be implemented."""
        for event_name, handler_names in SYNCHRONIZATIONS.items():
            for handler_name in handler_names:
                handler = get_handler(handler_name)
                assert callable(handler), f"Handler '{handler_name}' for '{event_name}' is not callable"

    def test_get_handler_raises_for_unknown(self):
        """get_handler should raise ValueError for unknown handlers."""
        with pytest.raises(ValueError) as exc_info:
            get_handler("nonexistent_handler")
        assert "Unknown handler" in str(exc_info.value)

    def test_handlers_dict_matches_registry_usage(self):
        """All handlers referenced in registry should be in HANDLERS dict."""
        all_handler_names = set()
        for handler_names in SYNCHRONIZATIONS.values():
            all_handler_names.update(handler_names)

        for handler_name in all_handler_names:
            assert handler_name in HANDLERS, f"Handler '{handler_name}' not in HANDLERS dict"


class TestHandlerSignatures:
    """Verify handler functions have correct signatures."""

    def test_handlers_accept_sender(self):
        """All handlers must accept 'sender' as first parameter."""
        for name, handler in HANDLERS.items():
            sig = inspect.signature(handler)
            params = list(sig.parameters.keys())
            assert "sender" in params, f"Handler '{name}' missing 'sender' parameter"

    def test_handlers_accept_kwargs(self):
        """All handlers must accept **kwargs for flexibility."""
        for name, handler in HANDLERS.items():
            sig = inspect.signature(handler)
            has_var_keyword = any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()
            )
            assert has_var_keyword, f"Handler '{name}' missing **kwargs"

    def test_embedding_handlers_require_content(self):
        """Embedding handlers need 'content' parameter."""
        embedding_handlers = [
            "generate_summary_embedding",
            "generate_challenge_embedding",
            "generate_approach_embedding",
        ]
        for handler_name in embedding_handlers:
            handler = get_handler(handler_name)
            sig = inspect.signature(handler)
            params = list(sig.parameters.keys())
            assert "content" in params, f"Handler '{handler_name}' missing 'content' parameter"

    def test_enqueue_handlers_use_kwargs(self):
        """V2 enqueue handlers accept idea_id via kwargs for flexibility."""
        enqueue_handlers = [
            "enqueue_connection",
            "enqueue_nurture",
            "enqueue_nurture_if_summary_only",
            "enqueue_surfacing_linked",
        ]
        for handler_name in enqueue_handlers:
            handler = get_handler(handler_name)
            sig = inspect.signature(handler)
            # V2 handlers use **kwargs to accept idea_id and other params
            has_var_keyword = any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()
            )
            assert has_var_keyword, f"Handler '{handler_name}' should accept **kwargs"


class TestSignalDefinitions:
    """Verify signals referenced in registry are defined."""

    def test_all_registry_signals_exist(self):
        """All event names in registry should be valid signals."""
        for event_name in SYNCHRONIZATIONS.keys():
            signal = get_signal(event_name)
            assert signal is not None, f"Signal '{event_name}' not found"

    def test_get_signal_creates_if_missing(self):
        """get_signal should create new signals on demand."""
        # This is blinker's behavior - it creates signals lazily
        signal = get_signal("test.nonexistent.signal")
        assert signal is not None

    def test_core_signals_are_predefined(self):
        """Core signals should be pre-defined for type hints."""
        from crabgrass.syncs.signals import (
            summary_created,
            summary_updated,
            idea_created,
            session_started,
            session_ended,
            # V2 signals
            objective_created,
            objective_updated,
            objective_retired,
            idea_linked_to_objective,
            idea_structure_added,
            agent_found_similarity,
            agent_found_relevant_user,
            agent_suggest_reconnection,
            agent_flag_orphan,
        )
        # Just verify these imports work
        assert summary_created is not None
        assert summary_updated is not None
        assert idea_created is not None
        assert session_started is not None
        assert session_ended is not None
        # V2 signals
        assert objective_created is not None
        assert objective_updated is not None
        assert objective_retired is not None
        assert idea_linked_to_objective is not None
        assert idea_structure_added is not None
        assert agent_found_similarity is not None
        assert agent_found_relevant_user is not None
        assert agent_suggest_reconnection is not None
        assert agent_flag_orphan is not None


class TestRegistryStructure:
    """Verify registry data structure is valid."""

    def test_registry_values_are_lists(self):
        """Each registry entry should be a list of handler names."""
        for event_name, handlers in SYNCHRONIZATIONS.items():
            assert isinstance(handlers, list), f"Handlers for '{event_name}' should be a list"

    def test_registry_values_are_non_empty(self):
        """Each registry entry should have at least one handler."""
        for event_name, handlers in SYNCHRONIZATIONS.items():
            assert len(handlers) > 0, f"'{event_name}' has no handlers"

    def test_registry_values_are_strings(self):
        """Handler names should be strings."""
        for event_name, handlers in SYNCHRONIZATIONS.items():
            for handler in handlers:
                assert isinstance(handler, str), f"Handler in '{event_name}' is not a string: {handler}"

    def test_no_duplicate_handlers_per_event(self):
        """Each event should not have duplicate handlers."""
        for event_name, handlers in SYNCHRONIZATIONS.items():
            unique_handlers = set(handlers)
            assert len(unique_handlers) == len(handlers), f"Duplicate handlers in '{event_name}'"
