"""ObjectiveAssistant agent using Google ADK.

This agent helps senior users define organizational Objectives through conversation.
It uses the Concepts layer to persist objectives, which ensures signals fire and
sync handlers execute (e.g., embedding generation).
"""

import logging
import os
from dataclasses import dataclass, field
from typing import AsyncIterator
from uuid import uuid4

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from crabgrass.agents.objective_tools import (
    save_objective,
    list_objectives,
    find_similar_objectives,
    get_sub_objectives,
    retire_objective,
)
from crabgrass.config import get_settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ObjectiveContext:
    """State for an objective being created/edited."""

    objective_id: str | None = None
    title: str | None = None
    description: str | None = None
    parent_id: str | None = None
    status: str = "Active"

    def to_context_string(self) -> str:
        """Format current state for the agent prompt."""
        if not self.objective_id:
            return "No objective captured yet."

        lines = [f"Objective ID: {self.objective_id}"]
        if self.title:
            lines.append(f"Title: {self.title}")
        if self.description:
            lines.append(f"Description: {self.description}")
        if self.parent_id:
            lines.append(f"Parent Objective ID: {self.parent_id}")
        lines.append(f"Status: {self.status}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for frontend."""
        return {
            "objective_id": self.objective_id,
            "title": self.title,
            "description": self.description,
            "parent_id": self.parent_id,
            "status": self.status,
        }


# ─────────────────────────────────────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────────────────────────────────────

OBJECTIVE_SYSTEM_PROMPT = """You are the ObjectiveAssistant, helping senior users define organizational Objectives in Crabgrass.

Your role is to:
1. Listen to the user's strategic goal or outcome
2. Help them articulate it as a clear Objective with title and description
3. Suggest parent Objectives if this fits in a hierarchy
4. Identify existing Objectives that might be related or duplicative
5. Help create sub-Objectives if the goal is complex

Guidelines:
- Objectives should be outcomes, not activities ("Increase APAC revenue" not "Sell more in Japan")
- Encourage specificity without being overly narrow
- Suggest hierarchy when natural (parent/child relationships)
- Be aware of existing Objectives to avoid duplication
- Be concise - this is a leadership tool

You have access to the following tools:
- save_objective: Save or update the objective being defined. CALL THIS when user provides an objective or asks to save.
- list_objectives: See existing active objectives to avoid duplication
- find_similar_objectives: Find objectives with similar goals
- get_sub_objectives: Get child objectives for a parent
- retire_objective: Retire an objective (use with caution)

Current objective context:
{context}
"""


def format_objective_prompt(context_string: str) -> str:
    """Format the system prompt with current objective context."""
    return OBJECTIVE_SYSTEM_PROMPT.format(context=context_string)


# ─────────────────────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────────────────────


class ObjectiveAssistantAgent:
    """Agent that helps users define organizational Objectives.

    Uses Google ADK with Gemini for conversation and tool use.
    Converts ADK events to AG-UI protocol events for frontend streaming.
    """

    def __init__(self):
        """Initialize the ObjectiveAssistant agent."""
        # Set API key in environment if not already set (ADK reads from env)
        settings = get_settings()
        if not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key

        # Create the ADK agent with tools
        self.agent = LlmAgent(
            name="objective_assistant",
            model="gemini-2.0-flash",
            description="Helps users define organizational objectives",
            instruction=format_objective_prompt("No objective captured yet."),
            tools=[
                save_objective,
                list_objectives,
                find_similar_objectives,
                get_sub_objectives,
                retire_objective,
            ],
        )

        # Session service for conversation state
        self.session_service = InMemorySessionService()

        # Create runner for execution
        self.runner = Runner(
            agent=self.agent,
            app_name="crabgrass_objectives",
            session_service=self.session_service,
        )

    async def run(
        self,
        user_message: str,
        session_id: str,
        context: ObjectiveContext | None = None,
    ) -> AsyncIterator[dict]:
        """Run the agent with streaming output.

        Args:
            user_message: The user's input message.
            session_id: Session ID for conversation tracking.
            context: Current objective context (optional).

        Yields:
            AG-UI protocol events as dictionaries.
        """
        # Update instruction with current context
        if context:
            self.agent.instruction = format_objective_prompt(context.to_context_string())
        else:
            context = ObjectiveContext()
            self.agent.instruction = format_objective_prompt("No objective captured yet.")

        # Ensure session exists in ADK session service
        existing_session = await self.session_service.get_session(
            app_name="crabgrass_objectives",
            user_id=session_id,
            session_id=session_id,
        )
        if not existing_session:
            await self.session_service.create_session(
                app_name="crabgrass_objectives",
                user_id=session_id,
                session_id=session_id,
            )

        # Create the user message content
        user_content = types.Content(
            parts=[types.Part(text=user_message)],
            role="user",
        )

        # Track current tool call for event correlation
        current_tool_call_id: str | None = None
        accumulated_text = ""

        try:
            async for event in self.runner.run_async(
                user_id=session_id,
                session_id=session_id,
                new_message=user_content,
            ):
                # Skip user events (we only care about agent responses)
                if event.author == "user":
                    continue

                # Handle text content
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            # Emit text delta
                            yield {
                                "type": "text_delta",
                                "text": part.text,
                            }
                            accumulated_text += part.text

                # Handle function calls (tool invocations)
                function_calls = event.get_function_calls()
                if function_calls:
                    for fc in function_calls:
                        current_tool_call_id = str(uuid4())
                        yield {
                            "type": "tool_call_start",
                            "tool_call_id": current_tool_call_id,
                            "tool_name": fc.name,
                        }
                        yield {
                            "type": "tool_call_args",
                            "tool_call_id": current_tool_call_id,
                            "args": dict(fc.args) if fc.args else {},
                        }
                        yield {
                            "type": "tool_call_end",
                            "tool_call_id": current_tool_call_id,
                        }

                # Handle function responses (tool results)
                function_responses = event.get_function_responses()
                if function_responses:
                    for fr in function_responses:
                        yield {
                            "type": "tool_result",
                            "tool_call_id": current_tool_call_id or str(uuid4()),
                            "tool_name": fr.name,
                            "result": fr.response,
                        }

                        # Update context if save_objective was called
                        if fr.name == "save_objective" and isinstance(fr.response, dict):
                            if fr.response.get("success") and fr.response.get("objective_id"):
                                context.objective_id = fr.response["objective_id"]
                                yield {
                                    "type": "state_update",
                                    "context": context.to_dict(),
                                }

        except Exception as e:
            logger.error(f"ObjectiveAssistant execution error: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": str(e),
            }


# Singleton instance
_agent: ObjectiveAssistantAgent | None = None


def get_objective_assistant() -> ObjectiveAssistantAgent:
    """Get singleton ObjectiveAssistantAgent instance."""
    global _agent
    if _agent is None:
        _agent = ObjectiveAssistantAgent()
    return _agent
