"""Concepts package - domain entities and their actions.

Each concept module defines:
- A dataclass representing the concept's state
- An Actions class with static methods for CRUD + domain operations
- Signals emitted when actions occur (wired via sync registry)
"""

from crabgrass.concepts.user import User, UserActions
from crabgrass.concepts.idea import Idea, IdeaActions, Status
from crabgrass.concepts.summary import Summary, SummaryActions
from crabgrass.concepts.challenge import Challenge, ChallengeActions
from crabgrass.concepts.approach import Approach, ApproachActions
from crabgrass.concepts.coherent_action import (
    CoherentAction,
    CoherentActionActions,
    ActionStatus,
)
from crabgrass.concepts.session import Session, SessionActions, Message, SessionStatus
from crabgrass.concepts.queue import QueueItem, QueueActions, QueueName, QueueItemStatus

# V2 Concepts
from crabgrass.concepts.objective import Objective, ObjectiveActions, ObjectiveStatus
from crabgrass.concepts.watch import Watch, WatchActions, WatchTargetType
from crabgrass.concepts.idea_objective import IdeaObjective, IdeaObjectiveActions
from crabgrass.concepts.notification import (
    Notification,
    NotificationActions,
    NotificationType,
)

__all__ = [
    # User
    "User",
    "UserActions",
    # Idea
    "Idea",
    "IdeaActions",
    "Status",
    # Summary
    "Summary",
    "SummaryActions",
    # Challenge
    "Challenge",
    "ChallengeActions",
    # Approach
    "Approach",
    "ApproachActions",
    # CoherentAction
    "CoherentAction",
    "CoherentActionActions",
    "ActionStatus",
    # Session
    "Session",
    "SessionActions",
    "Message",
    "SessionStatus",
    # Queue
    "QueueItem",
    "QueueActions",
    "QueueName",
    "QueueItemStatus",
    # V2: Objective
    "Objective",
    "ObjectiveActions",
    "ObjectiveStatus",
    # V2: Watch
    "Watch",
    "WatchActions",
    "WatchTargetType",
    # V2: IdeaObjective
    "IdeaObjective",
    "IdeaObjectiveActions",
    # V2: Notification
    "Notification",
    "NotificationActions",
    "NotificationType",
]
