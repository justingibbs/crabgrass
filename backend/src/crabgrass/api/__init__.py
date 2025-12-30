"""API package - HTTP routes and schemas."""

from crabgrass.api.ideas import router as ideas_router
from crabgrass.api.users import router as users_router
from crabgrass.api.agent import router as agent_router
from crabgrass.api.objectives import router as objectives_router
from crabgrass.api.notifications import router as notifications_router
from crabgrass.api.graph import router as graph_router

__all__ = [
    "ideas_router",
    "users_router",
    "agent_router",
    # V2
    "objectives_router",
    "notifications_router",
    "graph_router",
]
