"""Agent API router - SSE streaming endpoint for IdeaAssistant.

This router provides endpoints for chatting with the IdeaAssistant agent
using Server-Sent Events (SSE) with AG-UI protocol events.
"""

import json
import logging
from typing import AsyncIterator
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ag_ui.core.events import (
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    StateSnapshotEvent,
    CustomEvent,
)
from ag_ui.encoder import EventEncoder

from crabgrass.agents import get_idea_assistant, IdeaContext
from crabgrass.concepts.session import SessionActions
from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.summary import SummaryActions
from crabgrass.concepts.challenge import ChallengeActions
from crabgrass.concepts.approach import ApproachActions
from crabgrass.concepts.coherent_action import CoherentActionActions
from crabgrass.concepts.user import UserActions

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Schemas
# ─────────────────────────────────────────────────────────────────────────────


class AgentChatRequest(BaseModel):
    """Request to chat with the IdeaAssistant agent."""

    message: str
    session_id: str | None = None  # If None, creates new session
    idea_id: str | None = None  # If provided, loads existing idea context


class SessionResponse(BaseModel):
    """Response with session info."""

    session_id: str
    idea_id: str | None = None


class SessionDetail(BaseModel):
    """Detailed session information."""

    session_id: str
    idea_id: str | None
    status: str
    messages: list[dict]
    created_at: str | None
    updated_at: str | None


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def load_idea_context(idea_id: str) -> IdeaContext:
    """Load IdeaContext from an existing idea."""
    idea = IdeaActions.get_by_id(idea_id)
    if not idea:
        return IdeaContext()

    context = IdeaContext(
        idea_id=idea_id,
        title=idea.title,
        stage="initial",
    )

    # Load summary
    summary = SummaryActions.get_by_idea_id(idea_id)
    if summary:
        context.summary = summary.content
        context.stage = "summary"

    # Load challenge
    challenge = ChallengeActions.get_by_idea_id(idea_id)
    if challenge:
        context.challenge = challenge.content
        context.stage = "challenge"

    # Load approach
    approach = ApproachActions.get_by_idea_id(idea_id)
    if approach:
        context.approach = approach.content
        context.stage = "approach"

    # Load coherent actions
    actions = CoherentActionActions.list_by_idea_id(idea_id)
    if actions:
        context.coherent_actions = [a.content for a in actions]
        context.stage = "actions"

    # Check if complete
    if (
        context.summary
        and context.challenge
        and context.approach
        and context.coherent_actions
    ):
        context.stage = "complete"

    return context


async def stream_agent_response(
    message: str,
    session_id: str,
    context: IdeaContext,
) -> AsyncIterator[str]:
    """Stream agent response as SSE events.

    Yields AG-UI protocol events encoded as SSE data.
    """
    encoder = EventEncoder()
    agent = get_idea_assistant()
    run_id = str(uuid4())
    message_id = str(uuid4())

    # Record user message in session
    SessionActions.add_message(session_id, "user", message)

    # Emit RunStartedEvent
    yield encoder.encode(
        RunStartedEvent(
            thread_id=session_id,
            run_id=run_id,
        )
    )

    # Emit initial StateSnapshotEvent
    yield encoder.encode(
        StateSnapshotEvent(
            snapshot=context.to_dict(),
        )
    )

    # Emit TextMessageStartEvent
    yield encoder.encode(
        TextMessageStartEvent(
            message_id=message_id,
            role="assistant",
        )
    )

    # Collect full response for session tracking
    full_response: list[str] = []

    try:
        async for event in agent.run(message, session_id, context):
            event_type = event.get("type")

            if event_type == "text_delta":
                text = event.get("text", "")
                full_response.append(text)
                yield encoder.encode(
                    TextMessageContentEvent(
                        message_id=message_id,
                        delta=text,
                    )
                )

            elif event_type == "tool_call_start":
                yield encoder.encode(
                    ToolCallStartEvent(
                        toolCallId=event.get("tool_call_id", str(uuid4())),
                        toolCallName=event.get("tool_name", "unknown"),
                    )
                )

            elif event_type == "tool_call_args":
                args = event.get("args", {})
                yield encoder.encode(
                    ToolCallArgsEvent(
                        toolCallId=event.get("tool_call_id", ""),
                        delta=json.dumps(args) if args else "{}",
                    )
                )

            elif event_type == "tool_call_end":
                yield encoder.encode(
                    ToolCallEndEvent(
                        toolCallId=event.get("tool_call_id", ""),
                    )
                )

            elif event_type == "tool_result":
                result = event.get("result", {})
                yield encoder.encode(
                    ToolCallResultEvent(
                        messageId=message_id,
                        toolCallId=event.get("tool_call_id", ""),
                        content=json.dumps(result) if isinstance(result, dict) else str(result),
                    )
                )

                # Update context if save_idea was called successfully
                if isinstance(result, dict) and result.get("success"):
                    if result.get("idea_id"):
                        context.idea_id = result["idea_id"]

                # Emit updated StateSnapshotEvent after tool execution
                yield encoder.encode(
                    StateSnapshotEvent(
                        snapshot=context.to_dict(),
                    )
                )

            elif event_type == "state_update":
                # Direct state update from agent
                yield encoder.encode(
                    StateSnapshotEvent(
                        snapshot=event.get("context", context.to_dict()),
                    )
                )

            elif event_type == "suggestion":
                # Emit CustomEvent for suggestion proposals
                yield encoder.encode(
                    CustomEvent(
                        name="SUGGESTION",
                        value={
                            "suggestion_id": event.get("suggestion_id"),
                            "field": event.get("field"),
                            "content": event.get("content"),
                            "reason": event.get("reason", ""),
                        },
                    )
                )

            elif event_type == "error":
                error_msg = event.get("message", "Unknown error")
                full_response.append(f"\n\n[Error: {error_msg}]")
                yield encoder.encode(
                    TextMessageContentEvent(
                        message_id=message_id,
                        delta=f"\n\n[Error: {error_msg}]",
                    )
                )

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        error_text = f"\n\n[Error: {str(e)}]"
        full_response.append(error_text)
        yield encoder.encode(
            TextMessageContentEvent(
                message_id=message_id,
                delta=error_text,
            )
        )

    # Emit TextMessageEndEvent
    yield encoder.encode(
        TextMessageEndEvent(
            message_id=message_id,
        )
    )

    # Record assistant response in session
    assistant_response = "".join(full_response)
    if assistant_response:
        SessionActions.add_message(session_id, "assistant", assistant_response)

    # Emit RunFinishedEvent
    yield encoder.encode(
        RunFinishedEvent(
            thread_id=session_id,
            run_id=run_id,
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/chat", response_class=StreamingResponse)
async def chat_with_agent(request: AgentChatRequest):
    """Chat with the IdeaAssistant agent.

    Returns Server-Sent Events (SSE) stream with AG-UI protocol events.
    """
    current_user = UserActions.get_current()

    # Get or create session
    if request.session_id:
        session = SessionActions.get_by_id(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = session.id
        idea_id = session.idea_id or request.idea_id
    else:
        # Create new session
        session = SessionActions.start(
            user_id=current_user.id,
            idea_id=request.idea_id,
        )
        session_id = session.id
        idea_id = request.idea_id

    # Load idea context
    if idea_id:
        context = load_idea_context(idea_id)
    else:
        context = IdeaContext()

    return StreamingResponse(
        stream_agent_response(request.message, session_id, context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": session_id,
        },
    )


@router.post("/sessions", response_model=SessionResponse)
async def create_session(idea_id: str | None = None):
    """Create a new agent session.

    Optionally associate with an existing idea.
    """
    current_user = UserActions.get_current()

    # Validate idea exists if provided
    if idea_id:
        idea = IdeaActions.get_by_id(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

    session = SessionActions.start(
        user_id=current_user.id,
        idea_id=idea_id,
    )

    return SessionResponse(
        session_id=session.id,
        idea_id=idea_id,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    """Get session details including message history."""
    session = SessionActions.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDetail(
        session_id=session.id,
        idea_id=session.idea_id,
        status=session.status,
        messages=[
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
            }
            for m in session.messages
        ],
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None,
    )


@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str):
    """End/archive a session."""
    session = SessionActions.end(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "archived", "session_id": session_id}
