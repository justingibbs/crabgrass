"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from pydantic import BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# User Schemas
# ─────────────────────────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    name: str
    email: str
    role: str


# ─────────────────────────────────────────────────────────────────────────────
# Summary Schemas
# ─────────────────────────────────────────────────────────────────────────────


class SummaryCreate(BaseModel):
    """Schema for creating a summary."""

    content: str


class SummaryUpdate(BaseModel):
    """Schema for updating a summary."""

    content: str


class SummaryResponse(BaseModel):
    """Schema for summary response."""

    id: str
    content: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Challenge Schemas
# ─────────────────────────────────────────────────────────────────────────────


class ChallengeCreate(BaseModel):
    """Schema for creating a challenge."""

    content: str


class ChallengeUpdate(BaseModel):
    """Schema for updating a challenge."""

    content: str


class ChallengeResponse(BaseModel):
    """Schema for challenge response."""

    id: str
    content: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Approach Schemas
# ─────────────────────────────────────────────────────────────────────────────


class ApproachCreate(BaseModel):
    """Schema for creating an approach."""

    content: str


class ApproachUpdate(BaseModel):
    """Schema for updating an approach."""

    content: str


class ApproachResponse(BaseModel):
    """Schema for approach response."""

    id: str
    content: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# CoherentAction Schemas
# ─────────────────────────────────────────────────────────────────────────────


class CoherentActionCreate(BaseModel):
    """Schema for creating an action."""

    content: str


class CoherentActionUpdate(BaseModel):
    """Schema for updating an action."""

    content: str | None = None
    status: str | None = None


class CoherentActionResponse(BaseModel):
    """Schema for action response."""

    id: str
    content: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Idea Schemas
# ─────────────────────────────────────────────────────────────────────────────


class IdeaCreate(BaseModel):
    """Schema for creating an idea."""

    title: str
    summary: SummaryCreate


class IdeaUpdate(BaseModel):
    """Schema for updating an idea."""

    title: str | None = None
    status: str | None = None


class IdeaListItem(BaseModel):
    """Schema for idea list item (summary view)."""

    id: str
    title: str
    status: str
    author_id: str
    author_name: str
    created_at: datetime | None = None
    summary_preview: str | None = None


class IdeaDetail(BaseModel):
    """Schema for full idea detail."""

    id: str
    title: str
    status: str
    author_id: str
    author_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    summary: SummaryResponse | None = None
    challenge: ChallengeResponse | None = None
    approach: ApproachResponse | None = None
    coherent_actions: list[CoherentActionResponse] = []


# ─────────────────────────────────────────────────────────────────────────────
# Similarity Schemas
# ─────────────────────────────────────────────────────────────────────────────


class SimilarIdeaResponse(BaseModel):
    """Schema for similar idea response."""

    idea_id: str
    title: str
    similarity: float


# =============================================================================
# V2 SCHEMAS
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# Objective Schemas
# ─────────────────────────────────────────────────────────────────────────────


class ObjectiveCreate(BaseModel):
    """Schema for creating an objective."""

    title: str
    description: str
    parent_id: str | None = None


class ObjectiveUpdate(BaseModel):
    """Schema for updating an objective."""

    title: str | None = None
    description: str | None = None
    parent_id: str | None = None


class ObjectiveListItem(BaseModel):
    """Schema for objective list item (summary view)."""

    id: str
    title: str
    description: str
    status: str
    author_id: str
    author_name: str
    parent_id: str | None = None
    idea_count: int = 0
    created_at: datetime | None = None


class ObjectiveDetail(BaseModel):
    """Schema for full objective detail."""

    id: str
    title: str
    description: str
    status: str
    author_id: str
    author_name: str
    parent_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    idea_count: int = 0
    sub_objective_count: int = 0
    is_watched: bool = False


class SimilarObjectiveResponse(BaseModel):
    """Schema for similar objective response."""

    objective_id: str
    title: str
    similarity: float


# ─────────────────────────────────────────────────────────────────────────────
# Idea-Objective Link Schemas
# ─────────────────────────────────────────────────────────────────────────────


class LinkIdeaRequest(BaseModel):
    """Schema for linking an idea to an objective."""

    idea_id: str


class LinkedIdeaResponse(BaseModel):
    """Schema for a linked idea in objective context."""

    idea_id: str
    title: str
    status: str
    linked_at: datetime | None = None


class LinkedObjectiveResponse(BaseModel):
    """Schema for a linked objective in idea context."""

    objective_id: str
    title: str
    status: str
    linked_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Watch Schemas
# ─────────────────────────────────────────────────────────────────────────────


class WatchResponse(BaseModel):
    """Schema for watch response."""

    target_type: str
    target_id: str
    created_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Notification Schemas
# ─────────────────────────────────────────────────────────────────────────────


class NotificationResponse(BaseModel):
    """Schema for notification response."""

    id: str
    type: str
    message: str
    source_type: str
    source_id: str
    related_id: str | None = None
    read: bool
    created_at: datetime | None = None


class NotificationCountResponse(BaseModel):
    """Schema for notification count response."""

    unread_count: int
