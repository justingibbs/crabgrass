"""Agent API - chat endpoints for the IdeaAssistant agent.

Provides SSE streaming endpoints for real-time agent conversations.
"""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from crabgrass.agents import get_idea_assistant_agent
from crabgrass.concepts.session import SessionActions
from crabgrass.concepts.user import UserActions

logger = logging.getLogger(__name__)

router = APIRouter()

# Session service for ADK (in-memory for demo)
_session_service: InMemorySessionService | None = None
_runner: InMemoryRunner | None = None


def get_session_service() -> InMemorySessionService:
    """Get the singleton session service."""
    global _session_service
    if _session_service is None:
        _session_service = InMemorySessionService()
    return _session_service


def get_runner() -> InMemoryRunner:
    """Get the singleton runner instance."""
    global _runner
    if _runner is None:
        agent = get_idea_assistant_agent()
        _runner = InMemoryRunner(
            agent=agent,
            app_name="crabgrass",
        )
    return _runner


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str
    session_id: str | None = None
    idea_id: str | None = None


class ChatResponse(BaseModel):
    """Response body for non-streaming chat."""

    session_id: str
    response: str
    idea_id: str | None = None


class SessionResponse(BaseModel):
    """Response for session info."""

    session_id: str
    idea_id: str | None
    messages: list[dict]
    status: str


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Send a message to the IdeaAssistant agent.

    Returns an SSE stream of the agent's response.
    """
    try:
        runner = get_runner()
        current_user = UserActions.get_current()

        # Get or create session
        if request.session_id:
            session = SessionActions.get_by_id(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            session_id = session.id
            idea_id = session.idea_id
        else:
            # Create a new session
            session = SessionActions.start(
                user_id=current_user.id,
                idea_id=request.idea_id,
            )
            session_id = session.id
            idea_id = request.idea_id

        # Store user message in our session
        SessionActions.add_message(session_id, "user", request.message)

        # Prepare context for the agent
        context_parts = []
        if idea_id:
            from crabgrass.agents.tools import get_idea_context

            idea_context = get_idea_context(idea_id)
            if idea_context.get("status") == "success":
                context_parts.append(f"Current idea context: {json.dumps(idea_context['idea'])}")

        # Build the user message with context
        user_message = request.message
        if context_parts:
            user_message = f"{' | '.join(context_parts)}\n\nUser message: {request.message}"

        async def generate_sse() -> AsyncGenerator[str, None]:
            """Generate SSE events from the agent response."""
            full_response = []

            try:
                # Run the agent
                async for event in runner.run_async(
                    user_id=current_user.id,
                    session_id=session_id,
                    new_message=genai_types.Content(
                        role="user",
                        parts=[genai_types.Part(text=user_message)],
                    ),
                ):
                    # Handle different event types
                    event_type = type(event).__name__

                    if hasattr(event, "content") and event.content:
                        # Text content event
                        if hasattr(event.content, "parts"):
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    full_response.append(part.text)
                                    yield f"data: {json.dumps({'type': 'text_delta', 'data': {'delta': part.text}})}\n\n"

                    elif hasattr(event, "function_calls") and event.function_calls:
                        # Tool call event
                        for fc in event.function_calls:
                            tool_data = {
                                "type": "tool_call",
                                "data": {
                                    "name": fc.name if hasattr(fc, "name") else str(fc),
                                    "id": fc.id if hasattr(fc, "id") else None,
                                },
                            }
                            yield f"data: {json.dumps(tool_data)}\n\n"

                    elif hasattr(event, "function_responses") and event.function_responses:
                        # Tool response event
                        for fr in event.function_responses:
                            result_data = {
                                "type": "tool_result",
                                "data": {
                                    "name": fr.name if hasattr(fr, "name") else None,
                                    "result": fr.response if hasattr(fr, "response") else None,
                                },
                            }
                            yield f"data: {json.dumps(result_data)}\n\n"

                # Store assistant response in our session
                if full_response:
                    response_text = "".join(full_response)
                    SessionActions.add_message(session_id, "assistant", response_text)

                # Send completion event
                yield f"data: {json.dumps({'type': 'done', 'data': {'session_id': session_id}})}\n\n"

            except Exception as e:
                logger.error(f"Error in agent stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"

        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-Id": session_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest) -> ChatResponse:
    """Send a message to the IdeaAssistant agent (non-streaming).

    Returns the complete response after the agent finishes.
    Useful for simple integrations that don't need streaming.
    """
    try:
        runner = get_runner()
        current_user = UserActions.get_current()

        # Get or create session
        if request.session_id:
            session = SessionActions.get_by_id(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            session_id = session.id
            idea_id = session.idea_id
        else:
            session = SessionActions.start(
                user_id=current_user.id,
                idea_id=request.idea_id,
            )
            session_id = session.id
            idea_id = request.idea_id

        # Store user message
        SessionActions.add_message(session_id, "user", request.message)

        # Prepare context
        context_parts = []
        if idea_id:
            from crabgrass.agents.tools import get_idea_context

            idea_context = get_idea_context(idea_id)
            if idea_context.get("status") == "success":
                context_parts.append(f"Current idea context: {json.dumps(idea_context['idea'])}")

        user_message = request.message
        if context_parts:
            user_message = f"{' | '.join(context_parts)}\n\nUser message: {request.message}"

        # Run the agent and collect response
        full_response = []
        async for event in runner.run_async(
            user_id=current_user.id,
            session_id=session_id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_message)],
            ),
        ):
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            full_response.append(part.text)

        response_text = "".join(full_response)

        # Store assistant response
        if response_text:
            SessionActions.add_message(session_id, "assistant", response_text)

        return ChatResponse(
            session_id=session_id,
            response=response_text,
            idea_id=idea_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in sync chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """Get the chat history for a session."""
    session = SessionActions.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.id,
        idea_id=session.idea_id,
        messages=[
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
            }
            for m in session.messages
        ],
        status=session.status,
    )


@router.post("/chat/{session_id}/end")
async def end_session(session_id: str) -> dict:
    """End/archive a chat session."""
    session = SessionActions.end(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "success", "session_id": session_id}
