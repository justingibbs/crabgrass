# Crabgrass - AI Assistant Context

This file provides context for LLM coding assistants working on Crabgrass.

---

## What is Crabgrass?

Crabgrass is an **idea-to-innovation platform** that helps organizations capture, structure, and evolve ideas using AI agents. It transforms scattered human insights into structured strategic responses that can be reasoned about, connected, and surfaced to the right people.

**Core thesis:** Human insight + AI acceleration = Innovation

---

## Quick Reference

| Aspect | Details |
|--------|---------|
| **Backend** | Python 3.11+, FastAPI, Google ADK, DuckDB |
| **Frontend** | Next.js 15, React 19, AG-UI Protocol |
| **Package Manager** | uv (Python), npm (Node) |
| **Database** | DuckDB with VSS (vector) extension |
| **AI** | Gemini (LLM + embeddings) |
| **Architecture** | Concepts and Synchronizations |

---

## Context Files

Detailed documentation lives in `context/`. Read these before making significant changes:

| File | Purpose | Read When... |
|------|---------|--------------|
| `context/value-prop.md` | Why Crabgrass exists, the problem it solves | Understanding product direction |
| `context/tech-stack.md` | Technology choices and rationale | Adding dependencies, architectural questions |
| `context/concepts-synchronizations.md` | Core architecture: concepts, syncs, agents, queues | Modifying business logic, adding features |
| `context/wireframes.md` | UI screens and interaction flows | Working on frontend |
| `context/conventions.md` | Development conventions, uv commands, testing | Day-to-day development |
| `context/implementation-plan-demo-v1.md` | Detailed implementation plan for MVP | Building new features |

---

## Architecture Overview

Crabgrass uses **Concepts and Synchronizations** (MIT model):

```
┌─────────────────────────────────────────────────────────────┐
│  CONCEPTS (self-contained modules)                          │
│  ┌──────┐ ┌───────┐ ┌─────────┐ ┌────────┐ ┌─────────┐     │
│  │ Idea │ │Summary│ │Challenge│ │Approach│ │ Session │     │
│  └──┬───┘ └───┬───┘ └────┬────┘ └───┬────┘ └────┬────┘     │
│     └─────────┴──────────┴──────────┴───────────┘          │
│                          │                                  │
│                          ▼                                  │
│  SYNCHRONIZATIONS (declarative contracts)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  "summary.created" → ["generate_summary_embedding"]  │   │
│  │  "summary.updated" → ["generate_embedding", "find_similar"]│
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** The sync registry (`syncs/registry.py`) is the **single source of truth** for what happens when events fire. It's not documentation - changing it changes behavior.

---

## Common Commands

```bash
# Backend
cd backend
uv sync --dev                                    # Install dependencies
uv run uvicorn crabgrass.main:app --reload      # Run dev server
uv run pytest                                    # Run tests
uv add <package>                                 # Add dependency

# Frontend
cd frontend
npm install                                      # Install dependencies
npm run dev                                      # Run dev server
npm test                                         # Run tests
```

---

## Key Patterns

### Adding a New Concept

1. Create `concepts/<name>.py` with dataclass + actions
2. Add signals to `syncs/signals.py`
3. Add handlers to `syncs/handlers/`
4. Register in `syncs/handlers/__init__.py`
5. Add contracts to `syncs/registry.py`

### Adding a Sync Handler

1. Write handler function (no decorators)
2. Add to `HANDLERS` dict
3. Add contract to registry

### Concepts Emit, Registry Wires

```python
# Concept emits signal (doesn't know what listens)
summary_created.send(self, summary_id=id, content=content)

# Registry declares what happens (THE source of truth)
SYNCHRONIZATIONS = {
    "summary.created": ["generate_summary_embedding"],
}

# Wiring happens at startup (derived from registry)
register_all_syncs()
```

---

## Current Status

**Demo v1 scope:**
- Home dashboard with Ideas list
- Idea creation (chat with IdeaAssistantAgent)
- Idea detail (canvas + chat)
- Embeddings + similarity search
- DuckDB persistence

**Not yet implemented:**
- Objectives
- Background agents (Connection, Nurture, Surfacing)
- Notifications
- Multi-user

---

## Questions?

If you need more context:
1. Check the relevant file in `context/`
2. Search the codebase for existing patterns
3. Ask the user for clarification on product requirements
