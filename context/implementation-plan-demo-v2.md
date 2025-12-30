# Implementation Plan: Demo v2

This document outlines the implementation plan for Crabgrass Demo v2. Building on v1's foundation (Ideas, IdeaAssistantAgent, embeddings, similarity search), v2 introduces **Objectives**, **Background Agents**, **Notifications**, and **Graph Relationships**.

---

## Scope Summary

| In Scope (v2) | Out of Scope (Future) |
|---------------|----------------------|
| Objectives concept + screens | Comments |
| ObjectiveAssistantAgent | Real authentication |
| Background agents (Connection, Nurture, Surfacing, Objective) | AnalysisAgent (batch analytics) |
| Async queue system | Approval workflows |
| Notifications concept + UI column | Analytics dashboard |
| DuckPGQ graph relationships | External AI integration |
| Idea-Objective linking | Notification preferences |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend                                        │
│                          Next.js + AG-UI                                     │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐   │
│  │    Home     │  │  Objective  │  │  Objective  │  │   Notifications   │   │
│  │  Dashboard  │  │  Creation   │  │   Detail    │  │     Column        │   │
│  │ + Notifs    │  │   (Chat)    │  │  (+ Ideas)  │  │   (Real-time)     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ HTTP / SSE
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Backend / Agents                                   │
│                    FastAPI + Python + Google ADK                             │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          CONCEPTS                                      │  │
│  │  ┌──────┐ ┌───────┐ ┌─────────┐ ┌────────┐ ┌─────────┐ ┌───────────┐  │  │
│  │  │ Idea │ │Summary│ │Challenge│ │Approach│ │Objective│ │Notification│  │  │
│  │  └──┬───┘ └───┬───┘ └────┬────┘ └───┬────┘ └────┬────┘ └─────┬─────┘  │  │
│  │     └─────────┴──────────┴──────────┴───────────┴────────────┘        │  │
│  │                                    │                                   │  │
│  │                                    ▼                                   │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    SYNCHRONIZATIONS                              │  │  │
│  │  │         (Declarative contracts → Queue producers)                │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                           QUEUES                                       │  │
│  │  ┌──────────────┐ ┌────────────┐ ┌─────────────┐ ┌─────────────────┐  │  │
│  │  │ Connection   │ │  Nurture   │ │  Surfacing  │ │ ObjectiveReview │  │  │
│  │  │    Queue     │ │   Queue    │ │    Queue    │ │      Queue      │  │  │
│  │  └──────┬───────┘ └─────┬──────┘ └──────┬──────┘ └────────┬────────┘  │  │
│  │         │               │               │                  │           │  │
│  │         ▼               ▼               ▼                  ▼           │  │
│  │  ┌──────────────┐ ┌────────────┐ ┌─────────────┐ ┌─────────────────┐  │  │
│  │  │ Connection   │ │  Nurture   │ │  Surfacing  │ │   Objective     │  │  │
│  │  │    Agent     │ │   Agent    │ │    Agent    │ │     Agent       │  │  │
│  │  └──────────────┘ └────────────┘ └─────────────┘ └─────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     HUMAN-FACING AGENTS                                │  │
│  │  ┌───────────────────┐              ┌────────────────────────┐        │  │
│  │  │ IdeaAssistantAgent│              │ ObjectiveAssistantAgent│        │  │
│  │  │     (v1)          │              │         (v2)           │        │  │
│  │  └───────────────────┘              └────────────────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│                            ┌─────────────────┐                               │
│                            │   Gemini API    │                               │
│                            │ (LLM+Embeddings)│                               │
│                            └─────────────────┘                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DuckDB                                          │
│                                                                              │
│  ┌───────────────┐  ┌────────────────────┐  ┌────────────────────────────┐  │
│  │ Concept Tables│  │  DuckPGQ (Graph)   │  │      VSS (Vectors)         │  │
│  │ (Ideas, etc.) │  │  (Relationships)   │  │   (Similarity Search)      │  │
│  └───────────────┘  └────────────────────┘  └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## New Concepts for v2

### Objective Concept

```python
# concepts/objective.py

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from syncs.signals import objective_created, objective_updated, objective_retired

@dataclass
class Objective:
    """
    A desired outcome at any organizational level.
    Forms a flexible hierarchy via CONTRIBUTES_TO relationships.
    """
    id: str
    title: str
    description: str
    status: str  # Active, Retired
    author_id: str
    parent_id: str | None  # For hierarchy (optional)
    created_at: datetime
    updated_at: datetime


class ObjectiveActions:
    """Actions for the Objective concept."""

    def __init__(self, db):
        self.db = db

    def create(
        self,
        title: str,
        description: str,
        author_id: str,
        parent_id: str | None = None
    ) -> Objective:
        """
        Create a new Objective.

        Emits: objective.created
        Triggers (per registry): notify_parent_watchers (if parent exists)
        """
        objective_id = str(uuid4())
        objective = Objective(
            id=objective_id,
            title=title,
            description=description,
            status="Active",
            author_id=author_id,
            parent_id=parent_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.insert_objective(objective)

        objective_created.send(
            self,
            objective_id=objective_id,
            title=title,
            parent_id=parent_id,
            author_id=author_id
        )

        return objective

    def update(self, objective_id: str, **changes) -> Objective:
        """
        Update an Objective.

        Emits: objective.updated
        Triggers: notify_watchers
        """
        objective = self.db.update_objective(objective_id, **changes)
        objective_updated.send(self, objective_id=objective_id, changes=changes)
        return objective

    def retire(self, objective_id: str) -> Objective:
        """
        Retire an Objective (soft delete).

        Emits: objective.retired
        Triggers: add_linked_ideas_to_review_queue, notify_watchers
        """
        objective = self.db.update_objective(objective_id, status="Retired")
        objective_retired.send(self, objective_id=objective_id)
        return objective

    def get_by_id(self, objective_id: str) -> Objective:
        return self.db.get_objective(objective_id)

    def list_active(self) -> list[Objective]:
        return self.db.list_objectives(status="Active")

    def get_sub_objectives(self, objective_id: str) -> list[Objective]:
        """Get child objectives that CONTRIBUTE_TO this one."""
        return self.db.get_sub_objectives(objective_id)

    def get_linked_ideas(self, objective_id: str) -> list:
        """Get ideas that ADDRESS this objective."""
        return self.db.get_ideas_for_objective(objective_id)
```

### Notification Concept

```python
# concepts/notification.py

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
from enum import Enum

class NotificationType(str, Enum):
    SIMILAR_FOUND = "similar_found"
    IDEA_LINKED = "idea_linked"
    OBJECTIVE_RETIRED = "objective_retired"
    NURTURE_NUDGE = "nurture_nudge"
    CONTRIBUTION = "contribution"
    ORPHAN_ALERT = "orphan_alert"
    RECONNECTION_SUGGESTION = "reconnection_suggestion"

@dataclass
class Notification:
    """
    An alert for a user, created by agents based on events.
    """
    id: str
    user_id: str
    type: NotificationType
    message: str
    source_type: str  # "idea", "objective", "summary", etc.
    source_id: str
    related_id: str | None  # Optional related entity (e.g., similar idea)
    read: bool
    created_at: datetime


class NotificationActions:
    """Actions for the Notification concept."""

    def __init__(self, db):
        self.db = db

    def create(
        self,
        user_id: str,
        type: NotificationType,
        message: str,
        source_type: str,
        source_id: str,
        related_id: str | None = None
    ) -> Notification:
        """Create a notification for a user."""
        notification_id = str(uuid4())
        notification = Notification(
            id=notification_id,
            user_id=user_id,
            type=type,
            message=message,
            source_type=source_type,
            source_id=source_id,
            related_id=related_id,
            read=False,
            created_at=datetime.utcnow(),
        )
        self.db.insert_notification(notification)
        return notification

    def mark_read(self, notification_id: str) -> Notification:
        return self.db.update_notification(notification_id, read=True)

    def list_for_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        return self.db.list_notifications(user_id, unread_only=unread_only)
```

### Queue Concept

```python
# concepts/queue.py

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
from enum import Enum

class QueueName(str, Enum):
    CONNECTION = "connection"
    NURTURE = "nurture"
    SURFACING = "surfacing"
    OBJECTIVE_REVIEW = "objective_review"

class QueueItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class QueueItem:
    """
    An item in an async processing queue.
    """
    id: str
    queue: QueueName
    payload: dict  # JSON payload with event data
    status: QueueItemStatus
    attempts: int
    created_at: datetime
    processed_at: datetime | None


class QueueActions:
    """Actions for queue management."""

    def __init__(self, db):
        self.db = db

    def enqueue(self, queue: QueueName, payload: dict) -> QueueItem:
        """Add item to a queue."""
        item_id = str(uuid4())
        item = QueueItem(
            id=item_id,
            queue=queue,
            payload=payload,
            status=QueueItemStatus.PENDING,
            attempts=0,
            created_at=datetime.utcnow(),
            processed_at=None,
        )
        self.db.insert_queue_item(item)
        return item

    def dequeue(self, queue: QueueName, limit: int = 10) -> list[QueueItem]:
        """Get pending items from a queue and mark as processing."""
        items = self.db.get_pending_queue_items(queue, limit)
        for item in items:
            self.db.update_queue_item(item.id, status=QueueItemStatus.PROCESSING)
        return items

    def complete(self, item_id: str) -> QueueItem:
        """Mark item as completed."""
        return self.db.update_queue_item(
            item_id,
            status=QueueItemStatus.COMPLETED,
            processed_at=datetime.utcnow()
        )

    def fail(self, item_id: str) -> QueueItem:
        """Mark item as failed, increment attempts."""
        item = self.db.get_queue_item(item_id)
        return self.db.update_queue_item(
            item_id,
            status=QueueItemStatus.FAILED,
            attempts=item.attempts + 1
        )

    def retry_failed(self, queue: QueueName, max_attempts: int = 3) -> int:
        """Re-queue failed items under max attempts."""
        return self.db.retry_failed_items(queue, max_attempts)
```

---

## Updated Synchronizations Registry

The registry now produces queue items instead of calling handlers directly for background processing.

```python
# syncs/registry.py - v2

SYNCHRONIZATIONS = {
    # ─────────────────────────────────────────────────────────────────────────
    # Summary Changes
    # ─────────────────────────────────────────────────────────────────────────
    "summary.created": [
        "generate_summary_embedding",
        "enqueue_nurture",           # NEW: Add to NurtureQueue
    ],
    "summary.updated": [
        "generate_summary_embedding",
        "enqueue_connection",        # NEW: Add to ConnectionQueue
        "enqueue_nurture",           # NEW: Re-analyze for hints
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Challenge Changes
    # ─────────────────────────────────────────────────────────────────────────
    "challenge.created": [
        "generate_challenge_embedding",
        "enqueue_connection",        # NEW: Find similar challenges
    ],
    "challenge.updated": [
        "generate_challenge_embedding",
        "enqueue_connection",
        "enqueue_surfacing_shared_update",  # NEW: Notify Ideas sharing this
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Approach Changes
    # ─────────────────────────────────────────────────────────────────────────
    "approach.created": [
        "generate_approach_embedding",
        "enqueue_connection",        # NEW: Find similar approaches
    ],
    "approach.updated": [
        "generate_approach_embedding",
        "enqueue_connection",
        "enqueue_surfacing_shared_update",  # NEW: Notify Ideas sharing this
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Idea Lifecycle
    # ─────────────────────────────────────────────────────────────────────────
    "idea.created": [
        "enqueue_connection",        # Find similar ideas
        "enqueue_nurture_if_summary_only",  # NEW: Check if needs nurturing
    ],
    "idea.updated": [
        "enqueue_connection",
    ],
    "idea.archived": [
        "enqueue_surfacing_archived",  # NEW: Notify contributors
    ],
    "idea.linked_to_objective": [     # NEW
        "enqueue_surfacing_linked",    # Notify objective watchers
        "remove_from_nurture_queue",   # Idea is evolving
    ],
    "idea.structure_added": [         # NEW: Challenge/Approach added
        "remove_from_nurture_queue",   # No longer nascent
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Objective Lifecycle (NEW)
    # ─────────────────────────────────────────────────────────────────────────
    "objective.created": [
        "enqueue_surfacing_objective_created",  # Notify parent watchers
    ],
    "objective.updated": [
        "enqueue_surfacing_objective_updated",  # Notify watchers
    ],
    "objective.retired": [
        "enqueue_objective_review",             # Review linked ideas
        "enqueue_surfacing_objective_retired",  # Notify watchers
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Session Management
    # ─────────────────────────────────────────────────────────────────────────
    "session.started": [
        "log_session_start",
    ],
    "session.ended": [
        "log_session_end",
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # Agent Processing Results (NEW)
    # ─────────────────────────────────────────────────────────────────────────
    "agent.found_similarity": [
        "create_similarity_relationship",  # Graph edge
        "enqueue_surfacing_similarity",    # Notify users
    ],
    "agent.found_relevant_user": [
        "create_interest_relationship",    # Graph edge
        "enqueue_surfacing_interest",      # Notify user
    ],
    "agent.suggest_reconnection": [
        "enqueue_surfacing_reconnection",  # Notify for review
    ],
    "agent.flag_orphan": [
        "enqueue_surfacing_orphan",        # Alert contributors
    ],
}
```

---

## Queue Handler Implementations

### Enqueue Handlers (Sync → Queue)

```python
# syncs/handlers/enqueue.py

from concepts.queue import QueueActions, QueueName

def enqueue_connection(sender, **kwargs):
    """Add item to ConnectionQueue for relationship discovery."""
    queue = QueueActions(get_db())
    queue.enqueue(QueueName.CONNECTION, {
        "event": kwargs.get("_event_name"),
        "idea_id": kwargs.get("idea_id"),
        "summary_id": kwargs.get("summary_id"),
        "challenge_id": kwargs.get("challenge_id"),
        "approach_id": kwargs.get("approach_id"),
    })

def enqueue_nurture(sender, summary_id: str, idea_id: str, **kwargs):
    """Add Summary to NurtureQueue for analysis."""
    queue = QueueActions(get_db())
    queue.enqueue(QueueName.NURTURE, {
        "summary_id": summary_id,
        "idea_id": idea_id,
    })

def enqueue_nurture_if_summary_only(sender, idea_id: str, **kwargs):
    """Add to NurtureQueue only if idea has no structure yet."""
    db = get_db()
    idea = db.get_idea_with_details(idea_id)
    if idea.challenge is None and idea.approach is None:
        queue = QueueActions(db)
        queue.enqueue(QueueName.NURTURE, {
            "idea_id": idea_id,
            "reason": "summary_only",
        })

def enqueue_objective_review(sender, objective_id: str, **kwargs):
    """Add linked ideas to ObjectiveReviewQueue when objective retires."""
    db = get_db()
    linked_ideas = db.get_ideas_for_objective(objective_id)
    queue = QueueActions(db)
    for idea in linked_ideas:
        queue.enqueue(QueueName.OBJECTIVE_REVIEW, {
            "idea_id": idea.id,
            "retired_objective_id": objective_id,
        })

def enqueue_surfacing_linked(sender, idea_id: str, objective_id: str, **kwargs):
    """Queue notification for objective watchers when idea linked."""
    queue = QueueActions(get_db())
    queue.enqueue(QueueName.SURFACING, {
        "type": "idea_linked",
        "idea_id": idea_id,
        "objective_id": objective_id,
    })

def remove_from_nurture_queue(sender, idea_id: str, **kwargs):
    """Remove idea from NurtureQueue (it's evolving)."""
    db = get_db()
    db.remove_from_queue(QueueName.NURTURE, idea_id=idea_id)
```

---

## Background Agents

### Agent Runner Infrastructure

```python
# agents/runner.py

import asyncio
from abc import ABC, abstractmethod
from concepts.queue import QueueActions, QueueName, QueueItem

class BackgroundAgent(ABC):
    """Base class for background processing agents."""

    def __init__(self, db, queue_name: QueueName):
        self.db = db
        self.queue_name = queue_name
        self.queue = QueueActions(db)

    @abstractmethod
    async def process_item(self, item: QueueItem) -> None:
        """Process a single queue item. Implemented by subclasses."""
        pass

    async def run_once(self, batch_size: int = 10) -> int:
        """Process one batch of items. Returns count processed."""
        items = self.queue.dequeue(self.queue_name, limit=batch_size)
        processed = 0
        for item in items:
            try:
                await self.process_item(item)
                self.queue.complete(item.id)
                processed += 1
            except Exception as e:
                print(f"Error processing {item.id}: {e}")
                self.queue.fail(item.id)
        return processed

    async def run_loop(self, interval_seconds: float = 5.0):
        """Continuously process queue with polling interval."""
        while True:
            processed = await self.run_once()
            if processed == 0:
                await asyncio.sleep(interval_seconds)


class AgentOrchestrator:
    """Runs multiple background agents concurrently."""

    def __init__(self, agents: list[BackgroundAgent]):
        self.agents = agents

    async def start(self):
        """Start all agents as concurrent tasks."""
        tasks = [asyncio.create_task(agent.run_loop()) for agent in self.agents]
        await asyncio.gather(*tasks)
```

### ConnectionAgent

```python
# agents/connection_agent.py

from agents.runner import BackgroundAgent
from concepts.queue import QueueName, QueueItem
from services.similarity import SimilarityService
from services.graph import GraphService
from syncs.signals import agent_found_similarity, agent_found_relevant_user

class ConnectionAgent(BackgroundAgent):
    """
    Analyzes concepts to discover relationships.
    Finds similar Challenges, Approaches, related Ideas, and relevant Users.
    """

    def __init__(self, db):
        super().__init__(db, QueueName.CONNECTION)
        self.similarity = SimilarityService(db)
        self.graph = GraphService(db)

    async def process_item(self, item: QueueItem) -> None:
        payload = item.payload

        # Find similar content based on what triggered the event
        if payload.get("challenge_id"):
            await self._find_similar_challenges(payload["challenge_id"])
        elif payload.get("approach_id"):
            await self._find_similar_approaches(payload["approach_id"])
        elif payload.get("idea_id"):
            await self._find_related_ideas(payload["idea_id"])
            await self._find_relevant_users(payload["idea_id"])

    async def _find_similar_challenges(self, challenge_id: str):
        """Find challenges with similar content."""
        challenge = self.db.get_challenge(challenge_id)
        if not challenge.embedding:
            return

        similar = self.similarity.find_similar_challenges(
            challenge.embedding,
            exclude_id=challenge_id,
            threshold=0.75,
            limit=5
        )

        for match in similar:
            # Create graph relationship
            self.graph.create_relationship(
                from_type="challenge",
                from_id=challenge_id,
                to_type="challenge",
                to_id=match.id,
                relationship="IS_SIMILAR_TO",
                score=match.similarity_score
            )
            # Emit signal for surfacing
            agent_found_similarity.send(
                self,
                from_type="challenge",
                from_id=challenge_id,
                to_type="challenge",
                to_id=match.id,
                score=match.similarity_score
            )

    async def _find_similar_approaches(self, approach_id: str):
        """Find approaches with similar content."""
        approach = self.db.get_approach(approach_id)
        if not approach.embedding:
            return

        similar = self.similarity.find_similar_approaches(
            approach.embedding,
            exclude_id=approach_id,
            threshold=0.75,
            limit=5
        )

        for match in similar:
            self.graph.create_relationship(
                from_type="approach",
                from_id=approach_id,
                to_type="approach",
                to_id=match.id,
                relationship="IS_SIMILAR_TO",
                score=match.similarity_score
            )
            agent_found_similarity.send(
                self,
                from_type="approach",
                from_id=approach_id,
                to_type="approach",
                to_id=match.id,
                score=match.similarity_score
            )

    async def _find_related_ideas(self, idea_id: str):
        """Find ideas related via any kernel element."""
        idea = self.db.get_idea_with_details(idea_id)

        # Aggregate similarity across Summary, Challenge, Approach
        related = self.similarity.find_related_ideas(idea_id, threshold=0.7, limit=5)

        for match in related:
            self.graph.create_relationship(
                from_type="idea",
                from_id=idea_id,
                to_type="idea",
                to_id=match.id,
                relationship="IS_RELATED_TO",
                score=match.similarity_score
            )
            agent_found_similarity.send(
                self,
                from_type="idea",
                from_id=idea_id,
                to_type="idea",
                to_id=match.id,
                score=match.similarity_score
            )

    async def _find_relevant_users(self, idea_id: str):
        """Find users who might be interested based on their other work."""
        idea = self.db.get_idea_with_details(idea_id)

        # Find users who authored similar ideas
        relevant_users = self.similarity.find_users_with_similar_work(
            idea_id,
            exclude_author=idea.author_id,
            limit=3
        )

        for user in relevant_users:
            self.graph.create_relationship(
                from_type="user",
                from_id=user.id,
                to_type="idea",
                to_id=idea_id,
                relationship="MAY_BE_INTERESTED_IN",
                score=user.relevance_score
            )
            agent_found_relevant_user.send(
                self,
                user_id=user.id,
                idea_id=idea_id,
                score=user.relevance_score
            )
```

### NurtureAgent

```python
# agents/nurture_agent.py

from agents.runner import BackgroundAgent
from concepts.queue import QueueName, QueueItem, QueueActions
from services.embedding import EmbeddingService
from services.similarity import SimilarityService
from services.llm import LLMService
from syncs.signals import agent_found_similarity

class NurtureAgent(BackgroundAgent):
    """
    Monitors nascent Ideas (Summary only, no structure).
    Analyzes Summaries for hints of Challenges, finds similar Ideas,
    and queues gentle nudges encouraging users to evolve their Ideas.
    """

    def __init__(self, db):
        super().__init__(db, QueueName.NURTURE)
        self.similarity = SimilarityService(db)
        self.llm = LLMService()
        self.surfacing_queue = QueueActions(db)

    async def process_item(self, item: QueueItem) -> None:
        payload = item.payload
        idea_id = payload["idea_id"]

        idea = self.db.get_idea_with_details(idea_id)

        # Skip if idea has evolved (has structure now)
        if idea.challenge is not None or idea.approach is not None:
            return

        # 1. Analyze Summary for implicit Challenge
        await self._analyze_for_challenge(idea)

        # 2. Find similar nascent ideas
        await self._find_similar_summaries(idea)

        # 3. Suggest potential Objectives
        await self._suggest_objectives(idea)

    async def _analyze_for_challenge(self, idea):
        """Use LLM to detect implicit challenge in Summary."""
        if not idea.summary:
            return

        prompt = f"""Analyze this idea summary and identify if there's an implicit problem or challenge being described.

Summary: {idea.summary.content}

If you detect a clear problem statement or challenge, respond with:
CHALLENGE_DETECTED: [brief description of the challenge]

If no clear challenge is detected, respond with:
NO_CHALLENGE_DETECTED

Be concise."""

        response = await self.llm.generate(prompt)

        if "CHALLENGE_DETECTED:" in response:
            challenge_hint = response.split("CHALLENGE_DETECTED:")[1].strip()
            self.surfacing_queue.enqueue(QueueName.SURFACING, {
                "type": "nurture_nudge",
                "subtype": "challenge_hint",
                "idea_id": idea.id,
                "user_id": idea.author_id,
                "message": f"We noticed your idea might be addressing: {challenge_hint}. Want to make that explicit?",
            })

    async def _find_similar_summaries(self, idea):
        """Find other ideas with similar summaries."""
        if not idea.summary or not idea.summary.embedding:
            return

        similar = self.similarity.find_similar_summaries(
            idea.summary.embedding,
            exclude_idea_id=idea.id,
            threshold=0.7,
            limit=3
        )

        if similar:
            # Create graph relationships
            for match in similar:
                self.db.create_relationship(
                    from_type="summary",
                    from_id=idea.summary.id,
                    to_type="summary",
                    to_id=match.summary_id,
                    relationship="IS_SIMILAR_TO",
                    score=match.similarity_score
                )

            # Queue notification
            similar_titles = [m.idea_title for m in similar[:3]]
            self.surfacing_queue.enqueue(QueueName.SURFACING, {
                "type": "nurture_nudge",
                "subtype": "similar_ideas",
                "idea_id": idea.id,
                "user_id": idea.author_id,
                "message": f"Your idea may relate to: {', '.join(similar_titles)}",
                "related_idea_ids": [m.idea_id for m in similar],
            })

    async def _suggest_objectives(self, idea):
        """Suggest potentially relevant Objectives."""
        if not idea.summary:
            return

        # Get all active objectives
        objectives = self.db.list_objectives(status="Active")
        if not objectives:
            return

        # Use LLM to match
        obj_list = "\n".join([f"- {o.title}: {o.description}" for o in objectives])
        prompt = f"""Given this idea summary, which organizational objective (if any) seems most relevant?

Summary: {idea.summary.content}

Objectives:
{obj_list}

If there's a clear match, respond with:
MATCH: [objective title]

If no clear match, respond with:
NO_MATCH

Be selective - only suggest if there's genuine alignment."""

        response = await self.llm.generate(prompt)

        if "MATCH:" in response:
            obj_title = response.split("MATCH:")[1].strip()
            matched_obj = next((o for o in objectives if o.title in obj_title), None)
            if matched_obj:
                self.surfacing_queue.enqueue(QueueName.SURFACING, {
                    "type": "nurture_nudge",
                    "subtype": "objective_suggestion",
                    "idea_id": idea.id,
                    "user_id": idea.author_id,
                    "message": f"This Objective might be relevant: {matched_obj.title}",
                    "objective_id": matched_obj.id,
                })
```

### SurfacingAgent

```python
# agents/surfacing_agent.py

from agents.runner import BackgroundAgent
from concepts.queue import QueueName, QueueItem
from concepts.notification import NotificationActions, NotificationType

class SurfacingAgent(BackgroundAgent):
    """
    Reviews queue items and creates Notifications for relevant Users.
    Determines who should be alerted and how.
    """

    def __init__(self, db):
        super().__init__(db, QueueName.SURFACING)
        self.notifications = NotificationActions(db)

    async def process_item(self, item: QueueItem) -> None:
        payload = item.payload
        event_type = payload.get("type")

        handler = {
            "idea_linked": self._handle_idea_linked,
            "similar_found": self._handle_similar_found,
            "nurture_nudge": self._handle_nurture_nudge,
            "objective_created": self._handle_objective_created,
            "objective_retired": self._handle_objective_retired,
            "orphan_alert": self._handle_orphan_alert,
            "reconnection_suggestion": self._handle_reconnection,
        }.get(event_type)

        if handler:
            await handler(payload)

    async def _handle_idea_linked(self, payload: dict):
        """Notify objective watchers when idea linked."""
        objective_id = payload["objective_id"]
        idea_id = payload["idea_id"]

        idea = self.db.get_idea(idea_id)
        objective = self.db.get_objective(objective_id)
        watchers = self.db.get_objective_watchers(objective_id)

        for user in watchers:
            self.notifications.create(
                user_id=user.id,
                type=NotificationType.IDEA_LINKED,
                message=f"New idea '{idea.title}' linked to '{objective.title}'",
                source_type="objective",
                source_id=objective_id,
                related_id=idea_id,
            )

    async def _handle_similar_found(self, payload: dict):
        """Notify users when similar content found."""
        from_type = payload["from_type"]
        from_id = payload["from_id"]
        to_id = payload["to_id"]
        score = payload.get("score", 0)

        # Get authors of both items
        if from_type == "idea":
            from_idea = self.db.get_idea(from_id)
            to_idea = self.db.get_idea(to_id)

            # Notify both authors
            for author_id, other_title in [
                (from_idea.author_id, to_idea.title),
                (to_idea.author_id, from_idea.title)
            ]:
                self.notifications.create(
                    user_id=author_id,
                    type=NotificationType.SIMILAR_FOUND,
                    message=f"Similar idea found: '{other_title}'",
                    source_type="idea",
                    source_id=from_id,
                    related_id=to_id,
                )

    async def _handle_nurture_nudge(self, payload: dict):
        """Create nurture notification for idea author."""
        user_id = payload["user_id"]
        idea_id = payload["idea_id"]
        message = payload["message"]
        subtype = payload.get("subtype", "general")

        self.notifications.create(
            user_id=user_id,
            type=NotificationType.NURTURE_NUDGE,
            message=message,
            source_type="idea",
            source_id=idea_id,
            related_id=payload.get("related_idea_ids", [None])[0],
        )

    async def _handle_objective_created(self, payload: dict):
        """Notify parent objective watchers of new sub-objective."""
        objective_id = payload["objective_id"]
        parent_id = payload.get("parent_id")

        if parent_id:
            objective = self.db.get_objective(objective_id)
            watchers = self.db.get_objective_watchers(parent_id)

            for user in watchers:
                self.notifications.create(
                    user_id=user.id,
                    type=NotificationType.CONTRIBUTION,
                    message=f"New sub-objective created: '{objective.title}'",
                    source_type="objective",
                    source_id=parent_id,
                    related_id=objective_id,
                )

    async def _handle_objective_retired(self, payload: dict):
        """Notify watchers when objective retired."""
        objective_id = payload["objective_id"]
        objective = self.db.get_objective(objective_id)
        watchers = self.db.get_objective_watchers(objective_id)

        for user in watchers:
            self.notifications.create(
                user_id=user.id,
                type=NotificationType.OBJECTIVE_RETIRED,
                message=f"Objective retired: '{objective.title}'",
                source_type="objective",
                source_id=objective_id,
            )

    async def _handle_orphan_alert(self, payload: dict):
        """Alert contributors when idea loses objective link."""
        idea_id = payload["idea_id"]
        idea = self.db.get_idea(idea_id)
        contributors = self.db.get_idea_contributors(idea_id)

        for user in contributors:
            self.notifications.create(
                user_id=user.id,
                type=NotificationType.ORPHAN_ALERT,
                message=f"'{idea.title}' is no longer linked to an active Objective",
                source_type="idea",
                source_id=idea_id,
            )

    async def _handle_reconnection(self, payload: dict):
        """Suggest reconnecting orphaned idea to new objective."""
        idea_id = payload["idea_id"]
        objective_id = payload["objective_id"]

        idea = self.db.get_idea(idea_id)
        objective = self.db.get_objective(objective_id)
        contributors = self.db.get_idea_contributors(idea_id)
        obj_watchers = self.db.get_objective_watchers(objective_id)

        # Notify idea contributors
        for user in contributors:
            self.notifications.create(
                user_id=user.id,
                type=NotificationType.RECONNECTION_SUGGESTION,
                message=f"'{idea.title}' may align with '{objective.title}'",
                source_type="idea",
                source_id=idea_id,
                related_id=objective_id,
            )

        # Notify objective watchers
        for user in obj_watchers:
            self.notifications.create(
                user_id=user.id,
                type=NotificationType.RECONNECTION_SUGGESTION,
                message=f"Existing idea '{idea.title}' may be relevant",
                source_type="objective",
                source_id=objective_id,
                related_id=idea_id,
            )
```

### ObjectiveAgent

```python
# agents/objective_agent.py

from agents.runner import BackgroundAgent
from concepts.queue import QueueName, QueueItem, QueueActions
from services.llm import LLMService
from syncs.signals import agent_suggest_reconnection, agent_flag_orphan

class ObjectiveAgent(BackgroundAgent):
    """
    Reviews Ideas when Objectives change.
    When Objectives are retired, identifies orphaned Ideas and analyzes
    whether new or existing Objectives are relevant matches.
    """

    def __init__(self, db):
        super().__init__(db, QueueName.OBJECTIVE_REVIEW)
        self.llm = LLMService()
        self.surfacing_queue = QueueActions(db)

    async def process_item(self, item: QueueItem) -> None:
        payload = item.payload
        idea_id = payload["idea_id"]
        retired_objective_id = payload.get("retired_objective_id")

        idea = self.db.get_idea_with_details(idea_id)

        # Get all active objectives
        active_objectives = self.db.list_objectives(status="Active")

        # Find best matching objective
        best_match = await self._find_best_objective_match(idea, active_objectives)

        if best_match and best_match["score"] > 0.7:
            # Suggest reconnection
            agent_suggest_reconnection.send(
                self,
                idea_id=idea_id,
                objective_id=best_match["objective_id"],
                score=best_match["score"],
                reason=best_match["reason"],
            )
            self.surfacing_queue.enqueue(QueueName.SURFACING, {
                "type": "reconnection_suggestion",
                "idea_id": idea_id,
                "objective_id": best_match["objective_id"],
            })
        else:
            # Flag as orphan
            agent_flag_orphan.send(self, idea_id=idea_id)
            self.surfacing_queue.enqueue(QueueName.SURFACING, {
                "type": "orphan_alert",
                "idea_id": idea_id,
            })

    async def _find_best_objective_match(
        self,
        idea,
        objectives: list
    ) -> dict | None:
        """Use LLM to find best matching objective."""
        if not objectives:
            return None

        # Build context from idea
        idea_context = f"""
Title: {idea.title}
Summary: {idea.summary.content if idea.summary else 'N/A'}
Challenge: {idea.challenge.content if idea.challenge else 'N/A'}
Approach: {idea.approach.content if idea.approach else 'N/A'}
"""

        obj_list = "\n".join([
            f"ID: {o.id}\nTitle: {o.title}\nDescription: {o.description}\n"
            for o in objectives
        ])

        prompt = f"""Analyze this idea and determine which organizational objective (if any) it best aligns with.

IDEA:
{idea_context}

ACTIVE OBJECTIVES:
{obj_list}

Respond in this exact format:
MATCH_ID: [objective id or NONE]
SCORE: [0.0 to 1.0]
REASON: [brief explanation]

Be selective - only score above 0.7 if there's genuine strategic alignment."""

        response = await self.llm.generate(prompt)

        # Parse response
        try:
            lines = response.strip().split("\n")
            match_id = lines[0].split(":")[1].strip()
            score = float(lines[1].split(":")[1].strip())
            reason = lines[2].split(":")[1].strip()

            if match_id != "NONE":
                return {
                    "objective_id": match_id,
                    "score": score,
                    "reason": reason,
                }
        except:
            pass

        return None
```

---

## DuckPGQ Graph Schema

### Property Graph Definition

```sql
-- database/schema_graph.sql

-- Install and load PGQ extension
INSTALL pg_extension('duckpgq');
LOAD 'duckpgq';

-- Create property graph over existing tables
CREATE OR REPLACE PROPERTY GRAPH crabgrass_graph
VERTEX TABLES (
    users PROPERTIES (id, name, role),
    ideas PROPERTIES (id, title, status, author_id),
    summaries PROPERTIES (id, idea_id, content),
    challenges PROPERTIES (id, content),
    approaches PROPERTIES (id, content),
    objectives PROPERTIES (id, title, status),
    coherent_actions PROPERTIES (id, content, status)
)
EDGE TABLES (
    -- Idea structure edges (derived from FK relationships)
    (SELECT idea_id AS src, id AS dst, 'HAS_SUMMARY' AS rel FROM summaries)
        SOURCE KEY (src) REFERENCES ideas (id)
        DESTINATION KEY (dst) REFERENCES summaries (id)
        LABEL HAS_SUMMARY,

    (SELECT idea_id AS src, id AS dst, 'HAS_CHALLENGE' AS rel FROM idea_challenges)
        SOURCE KEY (src) REFERENCES ideas (id)
        DESTINATION KEY (dst) REFERENCES challenges (id)
        LABEL HAS_CHALLENGE,

    (SELECT idea_id AS src, id AS dst, 'HAS_APPROACH' AS rel FROM idea_approaches)
        SOURCE KEY (src) REFERENCES ideas (id)
        DESTINATION KEY (dst) REFERENCES approaches (id)
        LABEL HAS_APPROACH,

    -- User relationships
    (SELECT author_id AS src, id AS dst FROM ideas)
        SOURCE KEY (src) REFERENCES users (id)
        DESTINATION KEY (dst) REFERENCES ideas (id)
        LABEL AUTHORED,

    -- Idea-Objective links
    idea_objectives
        SOURCE KEY (idea_id) REFERENCES ideas (id)
        DESTINATION KEY (objective_id) REFERENCES objectives (id)
        LABEL ADDRESSES,

    -- Objective hierarchy
    (SELECT id AS src, parent_id AS dst FROM objectives WHERE parent_id IS NOT NULL)
        SOURCE KEY (src) REFERENCES objectives (id)
        DESTINATION KEY (dst) REFERENCES objectives (id)
        LABEL CONTRIBUTES_TO,

    -- Agent-discovered relationships (stored in relationships table)
    relationships
        SOURCE KEY (from_id) REFERENCES ideas (id)  -- Polymorphic, handled in queries
        DESTINATION KEY (to_id) REFERENCES ideas (id)
        LABEL IS_RELATED_TO PROPERTIES (score, discovered_at)
);
```

### Relationships Table

```sql
-- Table for agent-discovered relationships
CREATE TABLE IF NOT EXISTS relationships (
    id VARCHAR PRIMARY KEY,
    from_type VARCHAR NOT NULL,  -- 'idea', 'summary', 'challenge', 'approach', 'user'
    from_id VARCHAR NOT NULL,
    to_type VARCHAR NOT NULL,
    to_id VARCHAR NOT NULL,
    relationship VARCHAR NOT NULL,  -- 'IS_SIMILAR_TO', 'IS_RELATED_TO', 'MAY_BE_INTERESTED_IN'
    score FLOAT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    discovered_by VARCHAR,  -- Agent that created this
    UNIQUE (from_type, from_id, to_type, to_id, relationship)
);

-- Watch relationships
CREATE TABLE IF NOT EXISTS watches (
    user_id VARCHAR NOT NULL REFERENCES users(id),
    target_type VARCHAR NOT NULL,  -- 'idea', 'objective'
    target_id VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, target_type, target_id)
);

-- Contribution tracking
CREATE TABLE IF NOT EXISTS contributions (
    user_id VARCHAR NOT NULL REFERENCES users(id),
    idea_id VARCHAR NOT NULL REFERENCES ideas(id),
    contribution_type VARCHAR NOT NULL,  -- 'edit', 'comment'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, idea_id)
);

-- Idea-Objective links
CREATE TABLE IF NOT EXISTS idea_objectives (
    idea_id VARCHAR NOT NULL REFERENCES ideas(id),
    objective_id VARCHAR NOT NULL REFERENCES objectives(id),
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (idea_id, objective_id)
);
```

### Graph Query Service

```python
# services/graph.py

import duckdb
from typing import List, Optional

class GraphService:
    """Service for graph queries using DuckPGQ."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def create_relationship(
        self,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        relationship: str,
        score: float = None,
        discovered_by: str = None
    ):
        """Create or update a relationship edge."""
        conn = duckdb.connect(self.db_path)
        conn.execute("""
            INSERT INTO relationships (id, from_type, from_id, to_type, to_id, relationship, score, discovered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (from_type, from_id, to_type, to_id, relationship)
            DO UPDATE SET score = excluded.score, discovered_at = CURRENT_TIMESTAMP
        """, [
            str(uuid4()), from_type, from_id, to_type, to_id, relationship, score, discovered_by
        ])
        conn.close()

    def get_related_ideas(self, idea_id: str, limit: int = 10) -> List[dict]:
        """Get ideas related to given idea via graph traversal."""
        conn = duckdb.connect(self.db_path, read_only=True)

        # Use DuckPGQ path query
        query = """
        FROM GRAPH_TABLE (crabgrass_graph
            MATCH (i1:ideas WHERE i1.id = $1)-[r:IS_RELATED_TO]-(i2:ideas)
            COLUMNS (i2.id AS related_id, i2.title, r.score)
        )
        ORDER BY score DESC
        LIMIT $2
        """
        results = conn.execute(query, [idea_id, limit]).fetchall()
        conn.close()

        return [{"id": r[0], "title": r[1], "score": r[2]} for r in results]

    def get_ideas_sharing_challenge(self, challenge_id: str) -> List[dict]:
        """Find all ideas that share a challenge."""
        conn = duckdb.connect(self.db_path, read_only=True)

        query = """
        FROM GRAPH_TABLE (crabgrass_graph
            MATCH (i:ideas)-[:HAS_CHALLENGE]->(c:challenges WHERE c.id = $1)
            COLUMNS (i.id, i.title, i.status)
        )
        """
        results = conn.execute(query, [challenge_id]).fetchall()
        conn.close()

        return [{"id": r[0], "title": r[1], "status": r[2]} for r in results]

    def get_objective_idea_tree(self, objective_id: str) -> dict:
        """Get objective with all sub-objectives and their ideas."""
        conn = duckdb.connect(self.db_path, read_only=True)

        # Get objective hierarchy
        query = """
        FROM GRAPH_TABLE (crabgrass_graph
            MATCH (parent:objectives WHERE parent.id = $1)
                  <-[:CONTRIBUTES_TO*0..5]-(child:objectives)
            COLUMNS (child.id, child.title, child.status)
        )
        """
        objectives = conn.execute(query, [objective_id]).fetchall()

        # Get ideas for each objective
        result = {
            "objective_id": objective_id,
            "sub_objectives": [],
            "ideas": []
        }

        for obj in objectives:
            ideas_query = """
            FROM GRAPH_TABLE (crabgrass_graph
                MATCH (i:ideas)-[:ADDRESSES]->(o:objectives WHERE o.id = $1)
                COLUMNS (i.id, i.title, i.status)
            )
            """
            ideas = conn.execute(ideas_query, [obj[0]]).fetchall()
            result["sub_objectives"].append({
                "id": obj[0],
                "title": obj[1],
                "status": obj[2],
                "ideas": [{"id": i[0], "title": i[1], "status": i[2]} for i in ideas]
            })

        conn.close()
        return result

    def get_user_interest_graph(self, user_id: str) -> List[dict]:
        """Get ideas a user may be interested in (discovered by agents)."""
        conn = duckdb.connect(self.db_path, read_only=True)

        query = """
        SELECT
            r.to_id AS idea_id,
            i.title,
            r.score,
            r.discovered_at
        FROM relationships r
        JOIN ideas i ON r.to_id = i.id
        WHERE r.from_type = 'user'
          AND r.from_id = $1
          AND r.relationship = 'MAY_BE_INTERESTED_IN'
        ORDER BY r.score DESC, r.discovered_at DESC
        """
        results = conn.execute(query, [user_id]).fetchall()
        conn.close()

        return [{
            "idea_id": r[0],
            "title": r[1],
            "score": r[2],
            "discovered_at": r[3]
        } for r in results]

    def find_path_between_ideas(
        self,
        idea1_id: str,
        idea2_id: str,
        max_hops: int = 3
    ) -> Optional[List[dict]]:
        """Find shortest path between two ideas through any relationship."""
        conn = duckdb.connect(self.db_path, read_only=True)

        query = f"""
        FROM GRAPH_TABLE (crabgrass_graph
            MATCH p = SHORTEST (i1:ideas WHERE i1.id = $1)
                      -[*1..{max_hops}]-
                      (i2:ideas WHERE i2.id = $2)
            COLUMNS (vertices(p) AS path_nodes, edges(p) AS path_edges)
        )
        LIMIT 1
        """
        result = conn.execute(query, [idea1_id, idea2_id]).fetchone()
        conn.close()

        if result:
            return {"nodes": result[0], "edges": result[1]}
        return None
```

---

## ObjectiveAssistantAgent

```python
# agents/objective_assistant.py

from google import genai
from google.genai import types

OBJECTIVE_ASSISTANT_SYSTEM_PROMPT = """You are the ObjectiveAssistant, helping senior users define organizational Objectives in Crabgrass.

Your role is to:
1. Listen to the user's strategic goal or outcome
2. Help them articulate it as a clear Objective with title and description
3. Suggest parent Objectives if this fits in a hierarchy
4. Identify existing Objectives that might be related
5. Help create sub-Objectives if the goal is complex

Guidelines:
- Objectives should be outcomes, not activities ("Increase APAC revenue" not "Sell more in Japan")
- Encourage specificity without being overly narrow
- Suggest hierarchy when natural (parent/child relationships)
- Be aware of existing Objectives to avoid duplication
- Be concise - this is a leadership tool

You have access to the following tools:
- save_objective: Save or update the objective being defined
- list_objectives: See existing active objectives
- find_similar_objectives: Find objectives with similar goals

Current context will be provided with each message."""


class ObjectiveAssistantAgent:
    """Human-facing agent for creating and editing Objectives."""

    def __init__(self, db):
        self.db = db
        self.client = genai.Client()

    def create_tools(self):
        """Define tools available to the agent."""

        def save_objective(
            title: str,
            description: str,
            parent_id: str = None
        ) -> dict:
            """Save or update the objective being defined."""
            from concepts.objective import ObjectiveActions
            actions = ObjectiveActions(self.db)
            # Get current user from session context
            user_id = self.current_session.user_id
            objective = actions.create(
                title=title,
                description=description,
                author_id=user_id,
                parent_id=parent_id
            )
            return {
                "id": objective.id,
                "title": objective.title,
                "status": "created"
            }

        def list_objectives() -> list:
            """List all active objectives."""
            from concepts.objective import ObjectiveActions
            actions = ObjectiveActions(self.db)
            objectives = actions.list_active()
            return [{"id": o.id, "title": o.title, "description": o.description} for o in objectives]

        def find_similar_objectives(description: str) -> list:
            """Find objectives with similar descriptions."""
            from services.similarity import SimilarityService
            from services.embedding import EmbeddingService
            embedding = EmbeddingService().embed(description)
            similar = SimilarityService(self.db).find_similar_objectives(embedding, limit=5)
            return [{"id": s.id, "title": s.title, "similarity": s.score} for s in similar]

        return [save_objective, list_objectives, find_similar_objectives]

    async def chat(self, session_id: str, message: str) -> AsyncIterator[str]:
        """Process a message and stream the response."""
        # Load session
        session = self.db.get_session(session_id)
        self.current_session = session

        # Build context
        context = self._build_context(session)

        # Add user message to history
        session.messages.append({"role": "user", "content": message})

        # Call Gemini with tools
        response = await self.client.aio.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=self._build_contents(session.messages, context),
            config=types.GenerateContentConfig(
                system_instruction=OBJECTIVE_ASSISTANT_SYSTEM_PROMPT,
                tools=self.create_tools(),
            )
        )

        # Stream response
        full_response = ""
        async for chunk in response:
            if chunk.text:
                full_response += chunk.text
                yield chunk.text

            # Handle tool calls
            if chunk.candidates and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        result = await self._execute_tool(part.function_call)
                        yield f"\n[Tool: {part.function_call.name}]\n"

        # Save assistant message
        session.messages.append({"role": "assistant", "content": full_response})
        self.db.update_session(session_id, messages=session.messages)

    def _build_context(self, session) -> str:
        """Build context string for the agent."""
        objectives = self.db.list_objectives(status="Active")
        return f"""
Active Objectives ({len(objectives)}):
{chr(10).join([f"- {o.title}" for o in objectives[:10]])}
"""

    def _build_contents(self, messages: list, context: str) -> list:
        """Build contents array for Gemini."""
        contents = [{"role": "user", "parts": [{"text": f"Context:\n{context}"}]}]
        for msg in messages:
            contents.append({
                "role": msg["role"],
                "parts": [{"text": msg["content"]}]
            })
        return contents
```

---

## API Endpoints (v2 additions)

```python
# api/objectives.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/objectives", tags=["objectives"])

class ObjectiveCreate(BaseModel):
    title: str
    description: str
    parent_id: Optional[str] = None

class ObjectiveUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class ObjectiveResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    author_id: str
    author_name: str
    parent_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    idea_count: int

class ObjectiveDetailResponse(ObjectiveResponse):
    sub_objectives: List[ObjectiveResponse]
    ideas: List[IdeaListItem]

@router.get("")
async def list_objectives(status: str = "Active") -> List[ObjectiveResponse]:
    """List objectives, optionally filtered by status."""
    pass

@router.post("")
async def create_objective(data: ObjectiveCreate) -> ObjectiveResponse:
    """Create a new objective."""
    pass

@router.get("/{objective_id}")
async def get_objective(objective_id: str) -> ObjectiveDetailResponse:
    """Get objective with sub-objectives and linked ideas."""
    pass

@router.patch("/{objective_id}")
async def update_objective(objective_id: str, data: ObjectiveUpdate) -> ObjectiveResponse:
    """Update an objective."""
    pass

@router.post("/{objective_id}/retire")
async def retire_objective(objective_id: str) -> ObjectiveResponse:
    """Retire an objective (triggers review of linked ideas)."""
    pass

@router.post("/{objective_id}/watch")
async def watch_objective(objective_id: str) -> dict:
    """Add current user as watcher."""
    pass

@router.delete("/{objective_id}/watch")
async def unwatch_objective(objective_id: str) -> dict:
    """Remove current user as watcher."""
    pass
```

```python
# api/notifications.py

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

class NotificationResponse(BaseModel):
    id: str
    type: str
    message: str
    source_type: str
    source_id: str
    related_id: Optional[str]
    read: bool
    created_at: datetime

@router.get("")
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100)
) -> List[NotificationResponse]:
    """List notifications for current user."""
    pass

@router.post("/{notification_id}/read")
async def mark_read(notification_id: str) -> NotificationResponse:
    """Mark notification as read."""
    pass

@router.post("/read-all")
async def mark_all_read() -> dict:
    """Mark all notifications as read."""
    pass

@router.get("/stream")
async def notification_stream():
    """SSE stream for real-time notifications."""
    pass
```

```python
# api/ideas.py (additions)

@router.post("/{idea_id}/link-objective")
async def link_to_objective(idea_id: str, objective_id: str) -> IdeaDetail:
    """Link idea to an objective."""
    pass

@router.delete("/{idea_id}/link-objective/{objective_id}")
async def unlink_from_objective(idea_id: str, objective_id: str) -> IdeaDetail:
    """Remove idea-objective link."""
    pass

@router.get("/{idea_id}/related")
async def get_related_ideas(idea_id: str, limit: int = 10) -> List[SimilarIdea]:
    """Get related ideas via graph relationships."""
    pass
```

---

## Frontend Updates

### Updated Home Dashboard

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🦀 CRABGRASS                                   [ Sarah ◉ │ ○ VP Sales ]     │
│                                                  Frontline    Senior         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [+ New Idea]                                       [+ New Objective]        │
│                                                     (Senior only)            │
│                                                                              │
├────────────────────────┬─────────────────────────┬───────────────────────────┤
│  IDEAS                 │  OBJECTIVES             │  NOTIFICATIONS       🔴 3 │
├────────────────────────┼─────────────────────────┼───────────────────────────┤
│                        │                         │                           │
│ ┌────────────────────┐ │ ┌─────────────────────┐ │ ┌───────────────────────┐ │
│ │ Japan Partnership  │ │ │ Expand APAC Revenue │ │ │ 🔔 Similar Approach   │ │
│ │ Strategy           │ │ │ Active · 3 Ideas    │ │ │ found: "Japan         │ │
│ │ Draft · Sarah · 2h │ │ │   └─ Enter Japan    │ │ │ Partnership"          │ │
│ │ 🔗 Enter Japan     │ │ │      Market (1)     │ │ │ just now              │ │
│ └────────────────────┘ │ └─────────────────────┘ │ └───────────────────────┘ │
│                        │                         │                           │
│ ┌────────────────────┐ │ ┌─────────────────────┐ │ ┌───────────────────────┐ │
│ │ ERP Integration    │ │ │ AI-Native Product   │ │ │ 💡 Your idea may      │ │
│ │ Concept            │ │ │ Expansion           │ │ │ relate to Diana's     │ │
│ │ Active · Marcus·1d │ │ │ Active · 2 Ideas    │ │ │ "ERP Integration"     │ │
│ └────────────────────┘ │ └─────────────────────┘ │ │ 1h ago                │ │
│                        │                         │ └───────────────────────┘ │
│ ┌────────────────────┐ │                         │                           │
│ │ Clinical AI        │ │                         │ ┌───────────────────────┐ │
│ │ Assistant          │ │                         │ │ 💬 Consider adding    │ │
│ │ Draft · Diana · 3d │ │                         │ │ a Challenge to your   │ │
│ │ ⚠️ No Objective    │ │                         │ │ "Clinical AI" idea    │ │
│ └────────────────────┘ │                         │ │ 2d ago                │ │
│                        │                         │ └───────────────────────┘ │
│                        │                         │                           │
│                        │                         │ ┌───────────────────────┐ │
│                        │                         │ │ ⚠️ "Healthcare Data"  │ │
│                        │                         │ │ lost its Objective    │ │
│                        │                         │ │ link. Review?         │ │
│                        │                         │ │ 3d ago                │ │
│                        │                         │ └───────────────────────┘ │
│                        │                         │         ▼ older          │
└────────────────────────┴─────────────────────────┴───────────────────────────┘
```

### Notification Types & Icons

| Type | Icon | Example Message |
|------|------|-----------------|
| similar_found | 🔔 | "Similar Approach found: Japan Partnership" |
| idea_linked | 📎 | "New idea 'X' linked to 'APAC Revenue'" |
| nurture_nudge | 💡 | "Your idea may relate to Diana's" |
| nurture_nudge | 💬 | "Consider adding a Challenge to your idea" |
| orphan_alert | ⚠️ | "'Healthcare Data' lost its Objective link" |
| reconnection | 🔗 | "'X' may align with new Objective 'Y'" |
| objective_retired | 📦 | "Objective 'Healthcare' has been retired" |

### Idea Canvas Updates (Objective Linking)

```
┌─────────────────────────────────────────┐
│ LINKED OBJECTIVES                  [🔗] │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📊 Enter Japan Market           │    │
│  │    └─ Expand APAC Revenue       │    │
│  │    [Unlink]                     │    │
│  └─────────────────────────────────┘    │
│                                         │
│  + Link to another Objective...         │
│                                         │
└─────────────────────────────────────────┘
```

### Objective Detail Screen

(See wireframes.md - already specified)

### Real-time Notification Updates

```typescript
// hooks/useNotifications.ts

import { useEffect, useState } from 'react';

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // Initial fetch
    fetchNotifications();

    // SSE for real-time updates
    const eventSource = new EventSource('/api/notifications/stream');

    eventSource.onmessage = (event) => {
      const notification = JSON.parse(event.data);
      setNotifications(prev => [notification, ...prev]);
      setUnreadCount(prev => prev + 1);
    };

    return () => eventSource.close();
  }, []);

  const markRead = async (id: string) => {
    await fetch(`/api/notifications/${id}/read`, { method: 'POST' });
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  return { notifications, unreadCount, markRead };
}
```

---

## Database Schema Updates

```sql
-- database/schema_v2.sql

-- Objectives table
CREATE TABLE IF NOT EXISTS objectives (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Retired')),
    author_id VARCHAR NOT NULL REFERENCES users(id),
    parent_id VARCHAR REFERENCES objectives(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    type VARCHAR NOT NULL,
    message TEXT NOT NULL,
    source_type VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    related_id VARCHAR,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Queue items table
CREATE TABLE IF NOT EXISTS queue_items (
    id VARCHAR PRIMARY KEY,
    queue VARCHAR NOT NULL,
    payload JSON NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Indexes for queue processing
CREATE INDEX IF NOT EXISTS idx_queue_items_pending
ON queue_items (queue, status, created_at)
WHERE status = 'pending';

-- Indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user
ON notifications (user_id, read, created_at DESC);

-- Indexes for relationships
CREATE INDEX IF NOT EXISTS idx_relationships_from
ON relationships (from_type, from_id);

CREATE INDEX IF NOT EXISTS idx_relationships_to
ON relationships (to_type, to_id);
```

---

## Implementation Phases

### Phase 1: Foundation (Database + Queue Infrastructure)

1. **Database schema updates**
   - Add objectives table
   - Add notifications table
   - Add queue_items table
   - Add relationships table
   - Add watches, contributions, idea_objectives tables

2. **Queue concept implementation**
   - QueueItem dataclass
   - QueueActions (enqueue, dequeue, complete, fail)
   - Queue polling infrastructure

3. **Update sync handlers to use queues**
   - Modify existing handlers to enqueue instead of direct processing
   - Add new enqueue_* handlers

### Phase 2: Objectives Concept

1. **Objective concept**
   - Dataclass and actions
   - Signals (created, updated, retired)
   - Database operations

2. **ObjectiveAssistantAgent**
   - System prompt
   - Tools (save_objective, list_objectives, find_similar)
   - Chat streaming

3. **Idea-Objective linking**
   - Link/unlink actions
   - Update idea signals
   - Sync handlers for linking events

4. **API endpoints**
   - Objectives CRUD
   - Watch/unwatch
   - Retirement flow

### Phase 3: Background Agents

1. **Agent runner infrastructure**
   - BackgroundAgent base class
   - AgentOrchestrator
   - Polling loop

2. **ConnectionAgent**
   - Queue consumer
   - Similarity discovery
   - Relationship creation

3. **NurtureAgent**
   - Summary analysis
   - Challenge detection
   - Objective suggestions

4. **SurfacingAgent**
   - Notification creation
   - User targeting logic

5. **ObjectiveAgent**
   - Orphan detection
   - Reconnection suggestions

### Phase 4: Graph Database (DuckPGQ)

1. **Enable DuckPGQ extension**
   - Install and load extension
   - Define property graph

2. **Graph service**
   - Relationship creation
   - Path queries
   - Hierarchy traversal

3. **Update similarity service**
   - Use graph for related ideas
   - Multi-hop relationship discovery

### Phase 5: Notifications & Frontend

1. **Notification concept**
   - Dataclass and actions
   - API endpoints
   - SSE streaming

2. **Frontend: Notifications column**
   - Real-time updates
   - Notification cards
   - Mark read functionality

3. **Frontend: Objectives screens**
   - Objective creation (chat)
   - Objective detail
   - Objective list with hierarchy

4. **Frontend: Idea updates**
   - Objective linking in canvas
   - Related ideas display
   - Orphan warnings

### Phase 6: Integration & Polish

1. **End-to-end testing**
   - Queue processing verification
   - Notification delivery
   - Graph query correctness

2. **Demo scenarios**
   - Verify all scenarios work
   - Add seed data for demo

3. **Error handling**
   - Queue retry logic
   - Graceful degradation

---

## Demo Scenarios

### Scenario 1: Bottom-Up Discovery (v1 enhanced)

1. Sarah creates idea about Japan market
2. **ConnectionAgent** finds Jim's similar approach
3. **SurfacingAgent** notifies both Sarah and Jim
4. Notification appears in real-time
5. Sarah clicks notification, sees related idea

### Scenario 2: Objective-Linked Idea

1. VP Sales creates "Expand APAC Revenue" objective
2. Sarah links her Japan idea to this objective
3. VP Sales (watching objective) gets notification
4. VP clicks through, reviews structured idea

### Scenario 3: Nurturing a Nascent Idea

1. Marcus captures rough hunch (Summary only)
2. **NurtureAgent** analyzes, detects implicit Challenge
3. **SurfacingAgent** creates gentle nudge notification
4. Marcus sees: "We noticed your idea might be addressing..."
5. Later: "Your idea may relate to Diana's..."

### Scenario 4: Objective Retirement Flow

1. CEO retires "Expand into Healthcare" objective
2. **ObjectiveAgent** reviews 5 linked ideas
3. Finds 2 match new "AI-Native" objective
4. 3 flagged as orphans
5. Contributors notified with suggestions

### Scenario 5: Real-Time Notifications

1. User has dashboard open
2. Background agent discovers similarity
3. Notification appears without refresh
4. Unread badge updates
5. Click navigates to related content

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| Objectives persist and link to Ideas | Create objective, link idea, verify relationship |
| Background agents process queues | Items move from pending → completed |
| Notifications appear real-time | SSE delivers within 2 seconds |
| Graph queries return relationships | DuckPGQ traversals work correctly |
| ObjectiveAssistantAgent functional | Full chat flow for creating objectives |
| Orphan detection works | Retiring objective flags linked ideas |
| NurtureAgent suggests structure | Summary-only ideas get nudges |
| ConnectionAgent finds similarities | Related content discovered and linked |

---

## Future Enhancements (Post-v2)

1. **Comments** - Collaboration on ideas
2. **AnalysisAgent** - Batch pattern detection
3. **Real authentication** - OAuth/SSO
4. **Notification preferences** - User-configurable alerts
5. **Approval workflows** - Status gates with roles
6. **Analytics dashboard** - Aggregate insights
7. **External AI capture** - Import from ChatGPT, etc.
