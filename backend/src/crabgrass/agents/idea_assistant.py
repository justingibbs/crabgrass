"""IdeaAssistant agent using Google ADK.

This agent helps users capture and structure their ideas through conversation.
It uses the Concepts layer to persist ideas, which ensures signals fire and
sync handlers execute (e.g., embedding generation).
"""

import logging
import os
from typing import AsyncIterator
from uuid import uuid4

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from crabgrass.agents.state import IdeaContext
from crabgrass.agents.prompts import format_system_prompt
from crabgrass.agents.tools import save_idea, find_similar, add_action, propose_suggestion
from crabgrass.config import get_settings

logger = logging.getLogger(__name__)


class IdeaAssistantAgent:
    """Agent that helps users capture and structure ideas.

    Uses Google ADK with Gemini for conversation and tool use.
    Converts ADK events to AG-UI protocol events for frontend streaming.
    """

    def __init__(self):
        """Initialize the IdeaAssistant agent."""
        # Set API key in environment if not already set (ADK reads from env)
        settings = get_settings()
        if not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key

        # Create the ADK agent with tools
        self.agent = LlmAgent(
            name="idea_assistant",
            model="gemini-2.0-flash",
            description="Helps users capture and structure their ideas",
            instruction=format_system_prompt("No idea captured yet."),
            tools=[save_idea, find_similar, add_action, propose_suggestion],
        )

        # Session service for conversation state
        self.session_service = InMemorySessionService()

        # Create runner for execution
        self.runner = Runner(
            agent=self.agent,
            app_name="crabgrass",
            session_service=self.session_service,
        )

    async def run(
        self,
        user_message: str,
        session_id: str,
        context: IdeaContext | None = None,
    ) -> AsyncIterator[dict]:
        """Run the agent with streaming output.

        Args:
            user_message: The user's input message.
            session_id: Session ID for conversation tracking.
            context: Current idea context (optional).

        Yields:
            AG-UI protocol events as dictionaries.
        """
        # Update instruction with current context
        if context:
            self.agent.instruction = format_system_prompt(context.to_context_string())
        else:
            context = IdeaContext()
            self.agent.instruction = format_system_prompt("No idea captured yet.")

        # Ensure session exists in ADK session service
        existing_session = await self.session_service.get_session(
            app_name="crabgrass",
            user_id=session_id,
            session_id=session_id,
        )
        if not existing_session:
            await self.session_service.create_session(
                app_name="crabgrass",
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

                        # Update context if save_idea was called
                        if fr.name == "save_idea" and isinstance(fr.response, dict):
                            if fr.response.get("success") and fr.response.get("idea_id"):
                                context.idea_id = fr.response["idea_id"]
                                yield {
                                    "type": "state_update",
                                    "context": context.to_dict(),
                                }

                        # Emit suggestion event if propose_suggestion was called
                        if fr.name == "propose_suggestion" and isinstance(fr.response, dict):
                            if fr.response.get("success"):
                                yield {
                                    "type": "suggestion",
                                    "suggestion_id": fr.response.get("suggestion_id"),
                                    "field": fr.response.get("field"),
                                    "content": fr.response.get("content"),
                                    "reason": fr.response.get("reason", ""),
                                }

        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": str(e),
            }


# Singleton instance
_agent: IdeaAssistantAgent | None = None


def get_idea_assistant() -> IdeaAssistantAgent:
    """Get singleton IdeaAssistantAgent instance."""
    global _agent
    if _agent is None:
        _agent = IdeaAssistantAgent()
    return _agent
