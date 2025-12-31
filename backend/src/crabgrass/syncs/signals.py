"""Signal definitions for concept events.

Signals are the mechanism by which concepts emit events. Handlers are
connected to signals via the sync registry, not via decorators here.
"""

from blinker import Namespace

# Create a namespace for all sync signals
sync_signals = Namespace()


def get_signal(name: str):
    """Get or create a signal by name.

    This is used by the sync wiring to dynamically connect handlers.
    """
    return sync_signals.signal(name)


# ─────────────────────────────────────────────────────────────────────────────
# Idea signals
# ─────────────────────────────────────────────────────────────────────────────
idea_created = sync_signals.signal("idea.created")
idea_updated = sync_signals.signal("idea.updated")
idea_archived = sync_signals.signal("idea.archived")
idea_deleted = sync_signals.signal("idea.deleted")

# ─────────────────────────────────────────────────────────────────────────────
# Summary signals
# ─────────────────────────────────────────────────────────────────────────────
summary_created = sync_signals.signal("summary.created")
summary_updated = sync_signals.signal("summary.updated")

# ─────────────────────────────────────────────────────────────────────────────
# Challenge signals
# ─────────────────────────────────────────────────────────────────────────────
challenge_created = sync_signals.signal("challenge.created")
challenge_updated = sync_signals.signal("challenge.updated")
challenge_deleted = sync_signals.signal("challenge.deleted")

# ─────────────────────────────────────────────────────────────────────────────
# Approach signals
# ─────────────────────────────────────────────────────────────────────────────
approach_created = sync_signals.signal("approach.created")
approach_updated = sync_signals.signal("approach.updated")
approach_deleted = sync_signals.signal("approach.deleted")

# ─────────────────────────────────────────────────────────────────────────────
# CoherentAction signals
# ─────────────────────────────────────────────────────────────────────────────
action_created = sync_signals.signal("action.created")
action_updated = sync_signals.signal("action.updated")
action_completed = sync_signals.signal("action.completed")
action_deleted = sync_signals.signal("action.deleted")

# ─────────────────────────────────────────────────────────────────────────────
# Session signals
# ─────────────────────────────────────────────────────────────────────────────
session_started = sync_signals.signal("session.started")
session_message_added = sync_signals.signal("session.message_added")
session_ended = sync_signals.signal("session.ended")

# =============================================================================
# V2 SIGNALS
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# Objective signals
# ─────────────────────────────────────────────────────────────────────────────
objective_created = sync_signals.signal("objective.created")
objective_updated = sync_signals.signal("objective.updated")
objective_retired = sync_signals.signal("objective.retired")

# ─────────────────────────────────────────────────────────────────────────────
# Idea linking signals
# ─────────────────────────────────────────────────────────────────────────────
idea_linked_to_objective = sync_signals.signal("idea.linked_to_objective")
idea_unlinked_from_objective = sync_signals.signal("idea.unlinked_from_objective")
idea_structure_added = sync_signals.signal("idea.structure_added")

# ─────────────────────────────────────────────────────────────────────────────
# Agent processing result signals
# ─────────────────────────────────────────────────────────────────────────────
agent_found_similarity = sync_signals.signal("agent.found_similarity")
agent_found_relevant_user = sync_signals.signal("agent.found_relevant_user")
agent_suggest_reconnection = sync_signals.signal("agent.suggest_reconnection")
agent_flag_orphan = sync_signals.signal("agent.flag_orphan")
