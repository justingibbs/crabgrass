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
