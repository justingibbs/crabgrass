"""Graph API router - hybrid queries and graph traversal.

This API provides endpoints for:
- Graph traversal (similar ideas, objective hierarchies)
- Hybrid search (vector + graph combined)
- Scoped searches (within user's graph)
- Multi-hop queries (approaches → challenges, etc.)
"""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from crabgrass.services.graph import get_graph_service, SimilarityMatch, HybridMatch
from crabgrass.services.embedding import get_embedding_service
from crabgrass.services.graph_batch import GraphBatchJob

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────


class SimilarityMatchResponse(BaseModel):
    """Response for a similarity match."""

    idea_id: str
    title: str
    similarity: float
    match_type: str
    graph_distance: int | None = None
    shared_objectives: list[str] | None = None


class HybridMatchResponse(BaseModel):
    """Response for a hybrid search match."""

    idea_id: str
    title: str
    similarity_score: float
    graph_score: float
    combined_score: float
    match_type: str
    path: list[str] | None = None


class ObjectiveTreeNode(BaseModel):
    """A node in the objective tree."""

    id: str
    title: str
    status: str
    children: list["ObjectiveTreeNode"] = []


class ObjectiveAncestor(BaseModel):
    """An ancestor objective."""

    id: str
    title: str
    depth: int


class AlternativeApproachResponse(BaseModel):
    """Alternative approach with similar challenge."""

    idea_id: str
    idea_title: str
    challenge_similarity: float
    approach_id: str
    approach_preview: str | None


class RelatedChallengeResponse(BaseModel):
    """Challenge related to a similar approach."""

    challenge_id: str
    challenge_content: str
    idea_id: str
    idea_title: str
    approach_similarity: float


class GraphScopeResponse(BaseModel):
    """User's graph scope."""

    idea_ids: list[str]
    objective_ids: list[str]


class BatchJobResultResponse(BaseModel):
    """Result of running graph batch job."""

    idea_edges: int
    challenge_edges: int
    approach_edges: int
    duration_ms: int


# ─────────────────────────────────────────────────────────────────────────────
# Similar Ideas Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/ideas/{idea_id}/similar", response_model=list[SimilarityMatchResponse])
def get_similar_ideas(
    idea_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    min_score: float = Query(default=0.5, ge=0, le=1),
):
    """Get ideas similar to the given idea via graph edges.

    Returns ideas that have been discovered as similar by the ConnectionAgent.
    """
    graph_service = get_graph_service()
    matches = graph_service.get_similar_ideas(idea_id, limit=limit, min_score=min_score)

    return [
        SimilarityMatchResponse(
            idea_id=m.idea_id,
            title=m.title,
            similarity=m.similarity,
            match_type=m.match_type,
            graph_distance=m.graph_distance,
            shared_objectives=m.shared_objectives,
        )
        for m in matches
    ]


@router.get("/ideas/{idea_id}/objectives", response_model=list[dict])
def get_objectives_for_idea(idea_id: str):
    """Get all objectives linked to an idea."""
    graph_service = get_graph_service()
    return graph_service.get_objectives_for_idea(idea_id)


# ─────────────────────────────────────────────────────────────────────────────
# Hybrid Search Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/search/hybrid", response_model=list[HybridMatchResponse])
def hybrid_search(
    query: str,
    user_id: str | None = None,
    content_type: Literal["summary", "challenge", "approach"] = "summary",
    limit: int = Query(default=10, ge=1, le=50),
    vector_weight: float = Query(default=0.7, ge=0, le=1),
    graph_weight: float = Query(default=0.3, ge=0, le=1),
):
    """Hybrid search combining vector similarity with graph relationships.

    If user_id is provided, results are boosted based on shared objectives.
    """
    # Generate embedding for query
    embedding_service = get_embedding_service()
    embedding = embedding_service.embed(query)

    graph_service = get_graph_service()
    matches = graph_service.hybrid_search(
        embedding=embedding,
        user_id=user_id,
        content_type=content_type,
        limit=limit,
        vector_weight=vector_weight,
        graph_weight=graph_weight,
    )

    return [
        HybridMatchResponse(
            idea_id=m.idea_id,
            title=m.title,
            similarity_score=m.similarity_score,
            graph_score=m.graph_score,
            combined_score=m.combined_score,
            match_type=m.match_type,
            path=m.path,
        )
        for m in matches
    ]


@router.post("/search/scoped", response_model=list[SimilarityMatchResponse])
def scoped_search(
    query: str,
    user_id: str,
    content_type: Literal["summary", "challenge", "approach"] = "summary",
    limit: int = Query(default=10, ge=1, le=50),
    min_score: float = Query(default=0.5, ge=0, le=1),
):
    """Search within user's graph scope only.

    Only returns results from ideas the user has authored or is watching.
    """
    embedding_service = get_embedding_service()
    embedding = embedding_service.embed(query)

    graph_service = get_graph_service()
    matches = graph_service.find_similar_for_user(
        embedding=embedding,
        user_id=user_id,
        content_type=content_type,
        limit=limit,
        min_score=min_score,
    )

    return [
        SimilarityMatchResponse(
            idea_id=m.idea_id,
            title=m.title,
            similarity=m.similarity,
            match_type=m.match_type,
        )
        for m in matches
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Multi-Hop Query Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/approaches/{approach_id}/related-challenges",
    response_model=list[RelatedChallengeResponse],
)
def get_related_challenges(
    approach_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    min_score: float = Query(default=0.5, ge=0, le=1),
):
    """Find challenges associated with similar approaches.

    Multi-hop query: find similar approaches → get their ideas' challenges.
    Useful for discovering what problems others solve with similar approaches.
    """
    graph_service = get_graph_service()
    results = graph_service.find_similar_approaches_then_challenges(
        approach_id=approach_id,
        limit=limit,
        min_score=min_score,
    )

    return [
        RelatedChallengeResponse(
            challenge_id=r["challenge_id"],
            challenge_content=r["challenge_content"],
            idea_id=r["idea_id"],
            idea_title=r["idea_title"],
            approach_similarity=r["approach_similarity"],
        )
        for r in results
    ]


@router.get(
    "/ideas/{idea_id}/alternative-approaches",
    response_model=list[AlternativeApproachResponse],
)
def get_alternative_approaches(
    idea_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    min_score: float = Query(default=0.6, ge=0, le=1),
):
    """Find alternative approaches for similar challenges.

    Multi-hop query: find ideas with similar challenges → get their approaches.
    Useful for discovering different solutions to the same problem.
    """
    graph_service = get_graph_service()
    results = graph_service.find_ideas_with_similar_challenges_different_approaches(
        idea_id=idea_id,
        limit=limit,
        min_score=min_score,
    )

    return [
        AlternativeApproachResponse(
            idea_id=r["idea_id"],
            idea_title=r["idea_title"],
            challenge_similarity=r["challenge_similarity"],
            approach_id=r["approach_id"],
            approach_preview=r["approach_preview"],
        )
        for r in results
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Objective Hierarchy Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/objectives/{objective_id}/tree", response_model=ObjectiveTreeNode)
def get_objective_tree(objective_id: str):
    """Get the full tree structure under an objective."""
    graph_service = get_graph_service()
    tree = graph_service.get_objective_tree(objective_id)

    if not tree:
        raise HTTPException(status_code=404, detail="Objective not found")

    return ObjectiveTreeNode(**tree)


@router.get("/objectives/{objective_id}/ancestors", response_model=list[ObjectiveAncestor])
def get_objective_ancestors(objective_id: str):
    """Get all ancestor objectives (parents, grandparents, etc)."""
    graph_service = get_graph_service()
    return [
        ObjectiveAncestor(**a)
        for a in graph_service.get_objective_ancestors(objective_id)
    ]


@router.get("/objectives/{objective_id}/descendants", response_model=list[ObjectiveAncestor])
def get_objective_descendants(objective_id: str):
    """Get all descendant objectives (children, grandchildren, etc)."""
    graph_service = get_graph_service()
    return [
        ObjectiveAncestor(**d)
        for d in graph_service.get_objective_descendants(objective_id)
    ]


@router.get("/objectives/{objective_id}/ideas", response_model=list[str])
def get_ideas_for_objective(
    objective_id: str,
    include_children: bool = Query(default=True),
):
    """Get all idea IDs linked to an objective.

    If include_children is True, also includes ideas linked to child objectives.
    """
    graph_service = get_graph_service()
    return graph_service.get_ideas_for_objective(objective_id, include_children)


# ─────────────────────────────────────────────────────────────────────────────
# User Graph Scope Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/users/{user_id}/graph-scope", response_model=GraphScopeResponse)
def get_user_graph_scope(user_id: str):
    """Get the set of ideas and objectives in a user's graph scope.

    Returns IDs of ideas the user has authored or can access via watched objectives.
    """
    graph_service = get_graph_service()
    scope = graph_service.get_user_graph_scope(user_id)

    return GraphScopeResponse(
        idea_ids=list(scope["idea_ids"]),
        objective_ids=list(scope["objective_ids"]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Admin / Maintenance Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/admin/rebuild-graph", response_model=BatchJobResultResponse)
def rebuild_graph_edges():
    """Rebuild all graph similarity edges from relationships table.

    This is an admin endpoint that triggers the batch job to rebuild
    all graph_similar_* tables from the source relationships.
    """
    job = GraphBatchJob()
    result = job.run()

    return BatchJobResultResponse(
        idea_edges=result["idea_edges"],
        challenge_edges=result["challenge_edges"],
        approach_edges=result["approach_edges"],
        duration_ms=result["duration_ms"],
    )


@router.post("/admin/rebuild-objective-hierarchy", response_model=dict)
def rebuild_objective_hierarchy():
    """Rebuild objective hierarchy graph edges.

    Regenerates all graph_objective_hierarchy edges from objectives.parent_id.
    """
    job = GraphBatchJob()
    count = job.rebuild_objective_hierarchy()

    return {"edges_created": count}
