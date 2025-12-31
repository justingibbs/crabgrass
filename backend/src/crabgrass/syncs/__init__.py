"""Synchronizations package - wiring signals to handlers.

The sync system has three parts:
1. Signals (signals.py) - event definitions
2. Registry (registry.py) - THE source of truth for what happens when
3. Handlers (handlers/) - plain functions that do the work

This module provides register_all_syncs() which reads the registry
and wires handlers to signals at startup.
"""

import logging

from crabgrass.syncs.registry import SYNCHRONIZATIONS
from crabgrass.syncs.signals import get_signal
from crabgrass.syncs.handlers import get_handler

logger = logging.getLogger(__name__)


def register_all_syncs() -> None:
    """Wire up all synchronizations from the declarative registry.

    This is called once at app startup. The registry is the single
    source of truth - changing it changes behavior.
    """
    total_handlers = 0

    for event_name, handler_names in SYNCHRONIZATIONS.items():
        signal = get_signal(event_name)
        for handler_name in handler_names:
            try:
                handler = get_handler(handler_name)
                signal.connect(handler)
                total_handlers += 1
                logger.debug(f"Wired {handler_name} to {event_name}")
            except ValueError as e:
                logger.error(f"Failed to wire handler: {e}")

    logger.info(f"Registered {total_handlers} sync handlers for {len(SYNCHRONIZATIONS)} events")


__all__ = [
    "register_all_syncs",
    "SYNCHRONIZATIONS",
    "get_signal",
    "get_handler",
]
