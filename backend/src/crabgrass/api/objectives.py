"""API routes for Objectives."""

from fastapi import APIRouter, HTTPException

from crabgrass.concepts.objective import ObjectiveActions
from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.idea_objective import IdeaObjectiveActions
from crabgrass.concepts.watch import WatchActions
from crabgrass.concepts.user import UserActions
from crabgrass.services.similarity import SimilarityService
from crabgrass.services.embedding import get_embedding_service
from crabgrass.api.schemas import (
    ObjectiveCreate,
    ObjectiveUpdate,
    ObjectiveListItem,
    ObjectiveDetail,
    SimilarObjectiveResponse,
    LinkIdeaRequest,
    LinkedIdeaResponse,
    WatchResponse,
)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────


def get_author_name(author_id: str) -> str:
    """Get author name from ID."""
    user = UserActions.get_by_id(author_id)
    return user.name if user else "Unknown"


def get_objective_list_item(objective) -> ObjectiveListItem:
    """Convert Objective to list item response."""
    idea_count = IdeaObjectiveActions.count_ideas_for_objective(objective.id)
    return ObjectiveListItem(
        id=objective.id,
        title=objective.title,
        description=objective.description[:200] + "..." if len(objective.description) > 200 else objective.description,
        status=objective.status,
        author_id=objective.author_id,
        author_name=get_author_name(objective.author_id),
        parent_id=objective.parent_id,
        idea_count=idea_count,
        created_at=objective.created_at,
    )


def get_objective_detail(objective, user_id: str) -> ObjectiveDetail:
    """Convert Objective to detail response."""
    idea_count = IdeaObjectiveActions.count_ideas_for_objective(objective.id)
    sub_objectives = ObjectiveActions.get_sub_objectives(objective.id)
    is_watched = WatchActions.exists(user_id, "objective", objective.id)

    return ObjectiveDetail(
        id=objective.id,
        title=objective.title,
        description=objective.description,
        status=objective.status,
        author_id=objective.author_id,
        author_name=get_author_name(objective.author_id),
        parent_id=objective.parent_id,
        created_at=objective.created_at,
        updated_at=objective.updated_at,
        idea_count=idea_count,
        sub_objective_count=len(sub_objectives),
        is_watched=is_watched,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Objective CRUD
# ─────────────────────────────────────────────────────────────────────────────


@router.get("")
async def list_objectives(
    status: str = "Active",
    parent_id: str | None = None,
) -> list[ObjectiveListItem]:
    """List objectives with optional filters."""
    if status not in ("Active", "Retired"):
        status = "Active"

    objectives = ObjectiveActions.list_all(
        status=status,
        parent_id=parent_id if parent_id else None,
    )
    return [get_objective_list_item(o) for o in objectives]


@router.post("", status_code=201)
async def create_objective(data: ObjectiveCreate) -> ObjectiveDetail:
    """Create a new objective."""
    current_user = UserActions.get_current()

    # Validate parent if provided
    if data.parent_id:
        parent = ObjectiveActions.get_by_id(data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent objective not found")
        if parent.status == "Retired":
            raise HTTPException(status_code=400, detail="Cannot create sub-objective under retired objective")

    objective = ObjectiveActions.create(
        title=data.title,
        description=data.description,
        author_id=current_user.id,
        parent_id=data.parent_id,
    )

    return get_objective_detail(objective, current_user.id)


@router.get("/{objective_id}")
async def get_objective(objective_id: str) -> ObjectiveDetail:
    """Get a single objective by ID."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    current_user = UserActions.get_current()
    return get_objective_detail(objective, current_user.id)


@router.patch("/{objective_id}")
async def update_objective(objective_id: str, data: ObjectiveUpdate) -> ObjectiveDetail:
    """Update an objective."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    if objective.status == "Retired":
        raise HTTPException(status_code=400, detail="Cannot update retired objective")

    # Validate parent if changing
    if data.parent_id is not None and data.parent_id:
        if data.parent_id == objective_id:
            raise HTTPException(status_code=400, detail="Objective cannot be its own parent")
        parent = ObjectiveActions.get_by_id(data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent objective not found")
        if parent.status == "Retired":
            raise HTTPException(status_code=400, detail="Cannot set retired objective as parent")

    update_kwargs = {}
    if data.title is not None:
        update_kwargs["title"] = data.title
    if data.description is not None:
        update_kwargs["description"] = data.description
    if data.parent_id is not None:
        update_kwargs["parent_id"] = data.parent_id if data.parent_id else None

    if update_kwargs:
        objective = ObjectiveActions.update(objective_id, **update_kwargs)

    current_user = UserActions.get_current()
    return get_objective_detail(objective, current_user.id)


@router.post("/{objective_id}/retire")
async def retire_objective(objective_id: str) -> ObjectiveDetail:
    """Retire an objective."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    if objective.status == "Retired":
        raise HTTPException(status_code=400, detail="Objective is already retired")

    objective = ObjectiveActions.retire(objective_id)

    current_user = UserActions.get_current()
    return get_objective_detail(objective, current_user.id)


@router.delete("/{objective_id}", status_code=204)
async def delete_objective(objective_id: str):
    """Delete an objective (permanent, prefer retire instead)."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    ObjectiveActions.delete(objective_id)


# ─────────────────────────────────────────────────────────────────────────────
# Similarity
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{objective_id}/similar")
async def get_similar_objectives(
    objective_id: str,
    limit: int = 5,
) -> list[SimilarObjectiveResponse]:
    """Find objectives similar to this one."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    similarity_service = SimilarityService()
    similar = similarity_service.find_similar_for_objective(
        objective_id=objective_id,
        limit=min(max(1, limit), 20),
    )

    return [
        SimilarObjectiveResponse(
            objective_id=s.objective_id,
            title=s.title,
            similarity=round(s.similarity, 3),
        )
        for s in similar
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Idea Linking
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{objective_id}/ideas")
async def get_linked_ideas(objective_id: str) -> list[LinkedIdeaResponse]:
    """Get all ideas linked to this objective."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    links = IdeaObjectiveActions.list_by_objective(objective_id)

    result = []
    for link in links:
        idea = IdeaActions.get_by_id(link.idea_id)
        if idea:
            result.append(LinkedIdeaResponse(
                idea_id=idea.id,
                title=idea.title,
                status=idea.status,
                linked_at=link.linked_at,
            ))

    return result


@router.post("/{objective_id}/ideas", status_code=201)
async def link_idea(objective_id: str, data: LinkIdeaRequest) -> LinkedIdeaResponse:
    """Link an idea to this objective."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    if objective.status == "Retired":
        raise HTTPException(status_code=400, detail="Cannot link ideas to retired objective")

    idea = IdeaActions.get_by_id(data.idea_id)
    if not idea:
        raise HTTPException(status_code=400, detail="Idea not found")

    # Check if already linked
    if IdeaObjectiveActions.exists(data.idea_id, objective_id):
        raise HTTPException(status_code=400, detail="Idea is already linked to this objective")

    link = IdeaObjectiveActions.link(data.idea_id, objective_id)

    return LinkedIdeaResponse(
        idea_id=idea.id,
        title=idea.title,
        status=idea.status,
        linked_at=link.linked_at,
    )


@router.delete("/{objective_id}/ideas/{idea_id}", status_code=204)
async def unlink_idea(objective_id: str, idea_id: str):
    """Unlink an idea from this objective."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    if not IdeaObjectiveActions.exists(idea_id, objective_id):
        raise HTTPException(status_code=404, detail="Link not found")

    IdeaObjectiveActions.unlink(idea_id, objective_id)


# ─────────────────────────────────────────────────────────────────────────────
# Sub-objectives
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{objective_id}/sub-objectives")
async def get_sub_objectives(objective_id: str) -> list[ObjectiveListItem]:
    """Get child objectives that contribute to this one."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    sub_objectives = ObjectiveActions.get_sub_objectives(objective_id)
    return [get_objective_list_item(o) for o in sub_objectives]


# ─────────────────────────────────────────────────────────────────────────────
# Watch
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/{objective_id}/watch", status_code=201)
async def watch_objective(objective_id: str) -> WatchResponse:
    """Start watching an objective."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    current_user = UserActions.get_current()
    watch = WatchActions.create(current_user.id, "objective", objective_id)

    return WatchResponse(
        target_type="objective",
        target_id=objective_id,
        created_at=watch.created_at,
    )


@router.delete("/{objective_id}/watch", status_code=204)
async def unwatch_objective(objective_id: str):
    """Stop watching an objective."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    current_user = UserActions.get_current()
    if not WatchActions.exists(current_user.id, "objective", objective_id):
        raise HTTPException(status_code=404, detail="Not watching this objective")

    WatchActions.delete(current_user.id, "objective", objective_id)


@router.get("/{objective_id}/watchers")
async def get_objective_watchers(objective_id: str) -> list[str]:
    """Get list of user IDs watching this objective."""
    objective = ObjectiveActions.get_by_id(objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    return WatchActions.get_objective_watchers(objective_id)
