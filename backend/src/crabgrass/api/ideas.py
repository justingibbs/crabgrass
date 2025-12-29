"""Ideas API router - thin HTTP layer delegating to concepts."""

from fastapi import APIRouter, HTTPException, Query

from crabgrass.api.schemas import (
    IdeaCreate,
    IdeaUpdate,
    IdeaListItem,
    IdeaDetail,
    SummaryCreate,
    SummaryUpdate,
    SummaryResponse,
    ChallengeCreate,
    ChallengeUpdate,
    ChallengeResponse,
    ApproachCreate,
    ApproachUpdate,
    ApproachResponse,
    CoherentActionCreate,
    CoherentActionUpdate,
    CoherentActionResponse,
    SimilarIdeaResponse,
)
from crabgrass.concepts.idea import IdeaActions, Status
from crabgrass.concepts.summary import SummaryActions
from crabgrass.concepts.challenge import ChallengeActions
from crabgrass.concepts.approach import ApproachActions
from crabgrass.concepts.coherent_action import CoherentActionActions
from crabgrass.concepts.user import UserActions
from crabgrass.services.similarity import SimilarityService

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def get_author_name(author_id: str) -> str:
    """Get author name by ID."""
    user = UserActions.get_by_id(author_id)
    return user.name if user else "Unknown"


def get_idea_list_item(idea) -> IdeaListItem:
    """Convert Idea to IdeaListItem with preview."""
    summary = SummaryActions.get_by_idea_id(idea.id)
    summary_preview = None
    if summary and summary.content:
        summary_preview = summary.content[:100] + "..." if len(summary.content) > 100 else summary.content

    return IdeaListItem(
        id=idea.id,
        title=idea.title,
        status=idea.status,
        author_id=idea.author_id,
        author_name=get_author_name(idea.author_id),
        created_at=idea.created_at,
        summary_preview=summary_preview,
    )


def get_idea_detail(idea) -> IdeaDetail:
    """Convert Idea to full IdeaDetail."""
    summary = SummaryActions.get_by_idea_id(idea.id)
    challenge = ChallengeActions.get_by_idea_id(idea.id)
    approach = ApproachActions.get_by_idea_id(idea.id)
    actions = CoherentActionActions.list_by_idea_id(idea.id)

    return IdeaDetail(
        id=idea.id,
        title=idea.title,
        status=idea.status,
        author_id=idea.author_id,
        author_name=get_author_name(idea.author_id),
        created_at=idea.created_at,
        updated_at=idea.updated_at,
        summary=SummaryResponse(
            id=summary.id,
            content=summary.content,
            created_at=summary.created_at,
            updated_at=summary.updated_at,
        ) if summary else None,
        challenge=ChallengeResponse(
            id=challenge.id,
            content=challenge.content,
            created_at=challenge.created_at,
            updated_at=challenge.updated_at,
        ) if challenge else None,
        approach=ApproachResponse(
            id=approach.id,
            content=approach.content,
            created_at=approach.created_at,
            updated_at=approach.updated_at,
        ) if approach else None,
        coherent_actions=[
            CoherentActionResponse(
                id=action.id,
                content=action.content,
                status=action.status,
                created_at=action.created_at,
                updated_at=action.updated_at,
            )
            for action in actions
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Idea Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[IdeaListItem])
async def list_ideas(
    author_id: str | None = Query(None, description="Filter by author"),
    status: Status | None = Query(None, description="Filter by status"),
):
    """List all ideas with optional filters."""
    ideas = IdeaActions.list_all(author_id=author_id, status=status)
    return [get_idea_list_item(idea) for idea in ideas]


@router.post("", response_model=IdeaDetail)
async def create_idea(data: IdeaCreate):
    """Create a new idea with summary.

    Uses the current mock user as author.
    """
    # Get current user (mock for demo)
    current_user = UserActions.get_current()

    # Create idea
    idea = IdeaActions.create(title=data.title, author_id=current_user.id)

    # Create summary (triggers embedding sync)
    SummaryActions.create(idea_id=idea.id, content=data.summary.content)

    return get_idea_detail(idea)


@router.get("/{idea_id}", response_model=IdeaDetail)
async def get_idea(idea_id: str):
    """Get full idea details."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    return get_idea_detail(idea)


@router.patch("/{idea_id}", response_model=IdeaDetail)
async def update_idea(idea_id: str, data: IdeaUpdate):
    """Update idea title or status."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Only update if values provided
    updated = IdeaActions.update(
        idea_id=idea_id,
        title=data.title,
        status=data.status,
    )

    return get_idea_detail(updated)


@router.delete("/{idea_id}")
async def delete_idea(idea_id: str):
    """Delete an idea and all related data."""
    success = IdeaActions.delete(idea_id)
    if not success:
        raise HTTPException(status_code=404, detail="Idea not found")

    return {"status": "deleted", "idea_id": idea_id}


@router.get("/{idea_id}/similar", response_model=list[SimilarIdeaResponse])
async def find_similar_ideas(
    idea_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum results"),
):
    """Find ideas similar to this one."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    try:
        service = SimilarityService()
        similar = service.find_similar_for_idea(idea_id=idea_id, limit=limit)
        return [
            SimilarIdeaResponse(
                idea_id=s.idea_id,
                title=s.title,
                similarity=s.similarity,
            )
            for s in similar
        ]
    except Exception as e:
        # Log but don't fail - similarity is optional
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Summary Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/{idea_id}/summary", response_model=SummaryResponse)
async def create_summary(idea_id: str, data: SummaryCreate):
    """Create summary for an idea."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Check if summary already exists
    existing = SummaryActions.get_by_idea_id(idea_id)
    if existing:
        raise HTTPException(status_code=400, detail="Summary already exists")

    summary = SummaryActions.create(idea_id=idea_id, content=data.content)
    return SummaryResponse(
        id=summary.id,
        content=summary.content,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )


@router.patch("/{idea_id}/summary", response_model=SummaryResponse)
async def update_summary(idea_id: str, data: SummaryUpdate):
    """Update an idea's summary."""
    summary = SummaryActions.get_by_idea_id(idea_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    updated = SummaryActions.update(summary_id=summary.id, content=data.content)
    return SummaryResponse(
        id=updated.id,
        content=updated.content,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Challenge Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/{idea_id}/challenge", response_model=ChallengeResponse)
async def create_challenge(idea_id: str, data: ChallengeCreate):
    """Create challenge for an idea."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Check if challenge already exists
    existing = ChallengeActions.get_by_idea_id(idea_id)
    if existing:
        raise HTTPException(status_code=400, detail="Challenge already exists")

    challenge = ChallengeActions.create(idea_id=idea_id, content=data.content)
    return ChallengeResponse(
        id=challenge.id,
        content=challenge.content,
        created_at=challenge.created_at,
        updated_at=challenge.updated_at,
    )


@router.patch("/{idea_id}/challenge", response_model=ChallengeResponse)
async def update_challenge(idea_id: str, data: ChallengeUpdate):
    """Update an idea's challenge."""
    challenge = ChallengeActions.get_by_idea_id(idea_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    updated = ChallengeActions.update(challenge_id=challenge.id, content=data.content)
    return ChallengeResponse(
        id=updated.id,
        content=updated.content,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/{idea_id}/challenge")
async def delete_challenge(idea_id: str):
    """Delete an idea's challenge."""
    challenge = ChallengeActions.get_by_idea_id(idea_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    ChallengeActions.delete(challenge.id)
    return {"status": "deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# Approach Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/{idea_id}/approach", response_model=ApproachResponse)
async def create_approach(idea_id: str, data: ApproachCreate):
    """Create approach for an idea."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Check if approach already exists
    existing = ApproachActions.get_by_idea_id(idea_id)
    if existing:
        raise HTTPException(status_code=400, detail="Approach already exists")

    approach = ApproachActions.create(idea_id=idea_id, content=data.content)
    return ApproachResponse(
        id=approach.id,
        content=approach.content,
        created_at=approach.created_at,
        updated_at=approach.updated_at,
    )


@router.patch("/{idea_id}/approach", response_model=ApproachResponse)
async def update_approach(idea_id: str, data: ApproachUpdate):
    """Update an idea's approach."""
    approach = ApproachActions.get_by_idea_id(idea_id)
    if not approach:
        raise HTTPException(status_code=404, detail="Approach not found")

    updated = ApproachActions.update(approach_id=approach.id, content=data.content)
    return ApproachResponse(
        id=updated.id,
        content=updated.content,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/{idea_id}/approach")
async def delete_approach(idea_id: str):
    """Delete an idea's approach."""
    approach = ApproachActions.get_by_idea_id(idea_id)
    if not approach:
        raise HTTPException(status_code=404, detail="Approach not found")

    ApproachActions.delete(approach.id)
    return {"status": "deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# Coherent Action Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{idea_id}/actions", response_model=list[CoherentActionResponse])
async def list_actions(idea_id: str):
    """List all actions for an idea."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    actions = CoherentActionActions.list_by_idea_id(idea_id)
    return [
        CoherentActionResponse(
            id=action.id,
            content=action.content,
            status=action.status,
            created_at=action.created_at,
            updated_at=action.updated_at,
        )
        for action in actions
    ]


@router.post("/{idea_id}/actions", response_model=CoherentActionResponse)
async def create_action(idea_id: str, data: CoherentActionCreate):
    """Create a new action for an idea."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    action = CoherentActionActions.create(idea_id=idea_id, content=data.content)
    return CoherentActionResponse(
        id=action.id,
        content=action.content,
        status=action.status,
        created_at=action.created_at,
        updated_at=action.updated_at,
    )


@router.patch("/{idea_id}/actions/{action_id}", response_model=CoherentActionResponse)
async def update_action(idea_id: str, action_id: str, data: CoherentActionUpdate):
    """Update an action."""
    action = CoherentActionActions.get_by_id(action_id)
    if not action or action.idea_id != idea_id:
        raise HTTPException(status_code=404, detail="Action not found")

    updated = CoherentActionActions.update(
        action_id=action_id,
        content=data.content,
        status=data.status,
    )
    return CoherentActionResponse(
        id=updated.id,
        content=updated.content,
        status=updated.status,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.post("/{idea_id}/actions/{action_id}/complete", response_model=CoherentActionResponse)
async def complete_action(idea_id: str, action_id: str):
    """Mark an action as complete."""
    action = CoherentActionActions.get_by_id(action_id)
    if not action or action.idea_id != idea_id:
        raise HTTPException(status_code=404, detail="Action not found")

    completed = CoherentActionActions.complete(action_id)
    return CoherentActionResponse(
        id=completed.id,
        content=completed.content,
        status=completed.status,
        created_at=completed.created_at,
        updated_at=completed.updated_at,
    )


@router.delete("/{idea_id}/actions/{action_id}")
async def delete_action(idea_id: str, action_id: str):
    """Delete an action."""
    action = CoherentActionActions.get_by_id(action_id)
    if not action or action.idea_id != idea_id:
        raise HTTPException(status_code=404, detail="Action not found")

    CoherentActionActions.delete(action_id)
    return {"status": "deleted"}
