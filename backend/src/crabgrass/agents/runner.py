"""Background agent runner infrastructure.

This module provides the base class and orchestrator for running
background processing agents that consume from queues.

Background agents run in the same process as FastAPI (for demo simplicity)
and process queue items asynchronously.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Callable

from crabgrass.concepts.queue import QueueActions, QueueName, QueueItem, QueueItemStatus

logger = logging.getLogger(__name__)


class BackgroundAgent(ABC):
    """Base class for background processing agents.

    Subclasses implement process_item() to handle queue items.
    The runner manages polling, error handling, and lifecycle.
    """

    def __init__(self, queue_name: QueueName):
        """Initialize the agent.

        Args:
            queue_name: Which queue this agent processes
        """
        self.queue_name = queue_name
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def name(self) -> str:
        """Agent name for logging."""
        return self.__class__.__name__

    @abstractmethod
    async def process_item(self, item: QueueItem) -> None:
        """Process a single queue item.

        Implemented by subclasses. Should raise an exception on failure.

        Args:
            item: The queue item to process
        """
        pass

    async def run_once(self, batch_size: int = 10) -> int:
        """Process one batch of items.

        Args:
            batch_size: Maximum items to process in this batch

        Returns:
            Number of items processed
        """
        items = QueueActions.dequeue(self.queue_name, limit=batch_size)
        processed = 0

        for item in items:
            try:
                logger.debug(f"{self.name}: Processing item {item.id}")
                await self.process_item(item)
                QueueActions.complete(item.id)
                processed += 1
                logger.debug(f"{self.name}: Completed item {item.id}")
            except Exception as e:
                logger.error(f"{self.name}: Error processing item {item.id}: {e}")
                QueueActions.fail(item.id)

        return processed

    async def run_loop(self, interval_seconds: float = 5.0, batch_size: int = 10):
        """Continuously process queue with polling interval.

        Args:
            interval_seconds: Time to sleep when queue is empty
            batch_size: Maximum items per batch
        """
        self._running = True
        logger.info(f"{self.name}: Starting background loop (interval={interval_seconds}s)")

        while self._running:
            try:
                processed = await self.run_once(batch_size)

                if processed == 0:
                    # No items found, wait before polling again
                    await asyncio.sleep(interval_seconds)
                else:
                    logger.info(f"{self.name}: Processed {processed} items")
                    # Small yield to prevent CPU hogging
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.info(f"{self.name}: Received cancellation, stopping")
                break
            except Exception as e:
                logger.error(f"{self.name}: Unexpected error in loop: {e}")
                await asyncio.sleep(interval_seconds)

        logger.info(f"{self.name}: Background loop stopped")

    def stop(self):
        """Signal the agent to stop."""
        self._running = False
        if self._task:
            self._task.cancel()


class AgentOrchestrator:
    """Runs multiple background agents concurrently.

    Manages starting, stopping, and monitoring background agents.
    Runs in the same process as FastAPI for demo simplicity.
    """

    def __init__(self):
        self.agents: list[BackgroundAgent] = []
        self._tasks: list[asyncio.Task] = []
        self._running = False

    def register(self, agent: BackgroundAgent) -> None:
        """Register an agent to be run.

        Args:
            agent: The background agent to add
        """
        self.agents.append(agent)
        logger.info(f"AgentOrchestrator: Registered {agent.name}")

    async def start(self, interval_seconds: float = 5.0):
        """Start all registered agents as concurrent tasks.

        Args:
            interval_seconds: Polling interval for all agents
        """
        if self._running:
            logger.warning("AgentOrchestrator: Already running")
            return

        self._running = True
        logger.info(f"AgentOrchestrator: Starting {len(self.agents)} agents")

        for agent in self.agents:
            task = asyncio.create_task(
                agent.run_loop(interval_seconds=interval_seconds),
                name=f"agent_{agent.name}",
            )
            agent._task = task
            self._tasks.append(task)

        logger.info("AgentOrchestrator: All agents started")

    async def stop(self):
        """Stop all running agents."""
        if not self._running:
            return

        logger.info("AgentOrchestrator: Stopping all agents")
        self._running = False

        # Signal all agents to stop
        for agent in self.agents:
            agent.stop()

        # Wait for tasks to complete (with timeout)
        if self._tasks:
            try:
                await asyncio.wait(self._tasks, timeout=10.0)
            except Exception as e:
                logger.error(f"AgentOrchestrator: Error waiting for tasks: {e}")

            # Cancel any remaining tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()

        self._tasks.clear()
        logger.info("AgentOrchestrator: All agents stopped")

    def get_status(self) -> dict:
        """Get status of all agents and their queues."""
        status = {
            "running": self._running,
            "agents": [],
        }

        for agent in self.agents:
            queue_counts = QueueActions.count_by_status(agent.queue_name)
            agent_status = {
                "name": agent.name,
                "queue": agent.queue_name.value,
                "running": agent._running,
                "queue_pending": queue_counts.get(QueueItemStatus.PENDING.value, 0),
                "queue_processing": queue_counts.get(QueueItemStatus.PROCESSING.value, 0),
                "queue_completed": queue_counts.get(QueueItemStatus.COMPLETED.value, 0),
                "queue_failed": queue_counts.get(QueueItemStatus.FAILED.value, 0),
            }
            status["agents"].append(agent_status)

        return status


# ─────────────────────────────────────────────────────────────────────────────
# Singleton orchestrator
# ─────────────────────────────────────────────────────────────────────────────

_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
