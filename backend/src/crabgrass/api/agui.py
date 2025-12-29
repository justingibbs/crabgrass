"""AG-UI Protocol endpoint for the IdeaAssistant agent.

This module wraps the ADK agent with AG-UI middleware to enable
integration with CopilotKit and other AG-UI compatible frontends.
"""

from ag_ui_adk import ADKAgent

from crabgrass.agents import get_idea_assistant_agent


_agui_agent: ADKAgent | None = None


def get_agui_agent() -> ADKAgent:
    """Get the singleton AG-UI wrapped agent instance."""
    global _agui_agent
    if _agui_agent is None:
        adk_agent = get_idea_assistant_agent()
        _agui_agent = ADKAgent(
            adk_agent=adk_agent,
            app_name="crabgrass",
            user_id="demo_user",
            session_timeout_seconds=3600,
            use_in_memory_services=True,
        )
    return _agui_agent
