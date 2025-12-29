"""Users API router - mock user management for demo."""

from fastapi import APIRouter, HTTPException

from crabgrass.api.schemas import UserResponse
from crabgrass.concepts.user import UserActions

router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def list_users():
    """List all users."""
    users = UserActions.list_all()
    return [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        )
        for user in users
    ]


@router.get("/current", response_model=UserResponse)
async def get_current_user():
    """Get the current mock user."""
    user = UserActions.get_current()
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.post("/current/{user_id}", response_model=UserResponse)
async def set_current_user(user_id: str):
    """Set the current mock user (for role toggle)."""
    user = UserActions.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    UserActions.set_current(user_id)
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get a user by ID."""
    user = UserActions.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )
