# Implementation Plan: Demo v1

This document outlines the implementation plan for the first Crabgrass demo. The goal is a **minimal vertical slice** demonstrating the core idea capture and structuring workflow with AI assistance.

---

## Scope Summary

| In Scope | Out of Scope (Future) |
|----------|----------------------|
| Home dashboard with Ideas list | Objectives screens |
| Idea Creation screen (chat) | Background agents (Connection, Nurture, Surfacing) |
| Idea Detail screen (canvas + chat) | ObjectiveAssistantAgent |
| IdeaAssistantAgent | Notifications system |
| Vector embeddings + similarity search | Multi-user collaboration |
| DuckDB persistence | Comments |
| Mock role toggle (UI only) | Queues and async processing |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│                    Next.js + AG-UI                          │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Home     │  │    Idea     │  │       Idea          │  │
│  │  Dashboard  │  │  Creation   │  │      Detail         │  │
│  │             │  │   (Chat)    │  │  (Canvas + Chat)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP / SSE
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend / Agent                         │
│              FastAPI + Python + Google ADK                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    CONCEPTS                             ││
│  │  ┌──────┐ ┌───────┐ ┌─────────┐ ┌────────┐ ┌─────────┐ ││
│  │  │ Idea │ │Summary│ │Challenge│ │Approach│ │ Session │ ││
│  │  └──┬───┘ └───┬───┘ └────┬────┘ └───┬────┘ └────┬────┘ ││
│  │     │         │          │          │           │       ││
│  │     └─────────┴──────────┴──────────┴───────────┘       ││
│  │                          │                              ││
│  │                          ▼                              ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │              SYNCHRONIZATIONS                       │││
│  │  │  (Declarative contracts connecting concept events)  │││
│  │  └─────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────┘│
│                          │                                  │
│            ┌─────────────┴─────────────┐                    │
│            ▼                           ▼                    │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │ IdeaAssistant   │         │   Gemini API    │            │
│  │     Agent       │         │ (LLM+Embeddings)│            │
│  └─────────────────┘         └─────────────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        DuckDB                               │
│                                                             │
│  ┌───────────────┐  ┌────────────────────┐                  │
│  │ Concept Tables│  │  VSS Extension     │                  │
│  │ (Ideas, etc.) │  │  (Vector Search)   │                  │
│  └───────────────┘  └────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Concepts and Synchronizations Design

This architecture follows the [MIT Concepts and Synchronizations model](https://news.mit.edu/2025/mit-researchers-propose-new-model-for-legible-modular-software-1106). Instead of scattering feature logic across services, we:

1. **Concepts** are self-contained modules with their own state and actions
2. **Synchronizations** are explicit, declarative contracts that define how concepts interact

### Why This Matters

Traditional approaches bury integration logic in API endpoints or service layers. When you want to know "what happens when an Idea is created?", you have to grep through the codebase. With synchronizations as explicit contracts:

- The rules are **visible** in one place
- The system is **verifiable** (we can write tests against the contracts)
- Future expansion is **predictable** (add new syncs without modifying concepts)

### Concepts in Demo v1

| Concept | Purpose | State | Actions |
|---------|---------|-------|---------|
| **Idea** | Container for a strategic response | id, title, status, author_id, timestamps | create, update, archive, delete |
| **Summary** | Freeform description of an idea | id, idea_id, content, embedding | create, update |
| **Challenge** | Problem framing for an idea | id, idea_id, content, embedding | create, update, delete |
| **Approach** | Guiding policy to address challenge | id, idea_id, content, embedding | create, update, delete |
| **CoherentAction** | Specific implementation step | id, idea_id, content, status | create, update, complete, delete |
| **Session** | Agent conversation state | id, user_id, idea_id, messages, status | start, addMessage, end |

### Synchronizations in Demo v1

Synchronizations are **contracts** that fire when concept actions occur. The registry is the **single source of truth** - it's not documentation, it's the actual wiring.

```python
# syncs/registry.py - This IS the wiring, not documentation

SYNCHRONIZATIONS = {
    # ─────────────────────────────────────────────────────────────
    # Summary Changes
    # ─────────────────────────────────────────────────────────────
    "summary.created": [
        "generate_summary_embedding",
    ],
    "summary.updated": [
        "generate_summary_embedding",
        "find_similar_ideas",
    ],

    # ─────────────────────────────────────────────────────────────
    # Challenge Changes
    # ─────────────────────────────────────────────────────────────
    "challenge.created": [
        "generate_challenge_embedding",
    ],
    "challenge.updated": [
        "generate_challenge_embedding",
    ],

    # ─────────────────────────────────────────────────────────────
    # Approach Changes
    # ─────────────────────────────────────────────────────────────
    "approach.created": [
        "generate_approach_embedding",
    ],
    "approach.updated": [
        "generate_approach_embedding",
    ],

    # ─────────────────────────────────────────────────────────────
    # Idea Lifecycle
    # ─────────────────────────────────────────────────────────────
    "idea.created": [
        "find_similar_ideas",
    ],

    # ─────────────────────────────────────────────────────────────
    # Session Management (logging only in v1)
    # ─────────────────────────────────────────────────────────────
    "session.started": [
        "log_session_start",
    ],
    "session.ended": [
        "log_session_end",
    ],
}
```

### Synchronization Infrastructure

The sync system has three parts: signals, handlers, and the wiring that connects them.

```python
# syncs/signals.py - Signal definitions

from blinker import Namespace

sync_signals = Namespace()

def get_signal(name: str):
    """Get or create a signal by name."""
    return sync_signals.signal(name)

# Pre-define signals for type hints and discoverability
idea_created = sync_signals.signal('idea.created')
idea_updated = sync_signals.signal('idea.updated')
summary_created = sync_signals.signal('summary.created')
summary_updated = sync_signals.signal('summary.updated')
challenge_created = sync_signals.signal('challenge.created')
challenge_updated = sync_signals.signal('challenge.updated')
approach_created = sync_signals.signal('approach.created')
approach_updated = sync_signals.signal('approach.updated')
session_started = sync_signals.signal('session.started')
session_ended = sync_signals.signal('session.ended')
```

```python
# syncs/handlers/__init__.py - Handler registry

from .embedding import (
    generate_summary_embedding,
    generate_challenge_embedding,
    generate_approach_embedding,
)
from .similarity import find_similar_ideas
from .logging import log_session_start, log_session_end

# Handler lookup by name - maps registry strings to functions
HANDLERS = {
    "generate_summary_embedding": generate_summary_embedding,
    "generate_challenge_embedding": generate_challenge_embedding,
    "generate_approach_embedding": generate_approach_embedding,
    "find_similar_ideas": find_similar_ideas,
    "log_session_start": log_session_start,
    "log_session_end": log_session_end,
}

def get_handler(name: str):
    """Get handler function by name."""
    if name not in HANDLERS:
        raise ValueError(f"Unknown handler: {name}")
    return HANDLERS[name]
```

```python
# syncs/handlers/embedding.py - Embedding handlers (no decorators!)

from services.embedding import EmbeddingService
from database import get_db

def generate_summary_embedding(sender, summary_id: str, content: str, **kwargs):
    """Generate and store embedding for a Summary."""
    embedding = EmbeddingService().embed(content)
    db = get_db()
    db.execute(
        "UPDATE summaries SET embedding = ? WHERE id = ?",
        [embedding, summary_id]
    )

def generate_challenge_embedding(sender, challenge_id: str, content: str, **kwargs):
    """Generate and store embedding for a Challenge."""
    embedding = EmbeddingService().embed(content)
    db = get_db()
    db.execute(
        "UPDATE challenges SET embedding = ? WHERE id = ?",
        [embedding, challenge_id]
    )

def generate_approach_embedding(sender, approach_id: str, content: str, **kwargs):
    """Generate and store embedding for an Approach."""
    embedding = EmbeddingService().embed(content)
    db = get_db()
    db.execute(
        "UPDATE approaches SET embedding = ? WHERE id = ?",
        [embedding, approach_id]
    )
```

```python
# syncs/handlers/similarity.py - Similarity handlers

from services.similarity import SimilarityService

def find_similar_ideas(sender, idea_id: str, **kwargs):
    """Find ideas similar to the given idea."""
    similar = SimilarityService().find_similar_for_idea(idea_id)
    # In demo v1: result is available to caller
    # In future: would queue for SurfacingAgent
    return similar
```

```python
# syncs/__init__.py - Wiring derived from registry (THE KEY PART)

from .registry import SYNCHRONIZATIONS
from .signals import get_signal
from .handlers import get_handler

def register_all_syncs():
    """
    Wire up all synchronizations from the declarative registry.

    This is called once at app startup. The registry is the single
    source of truth - changing it changes behavior.
    """
    for event_name, handler_names in SYNCHRONIZATIONS.items():
        signal = get_signal(event_name)
        for handler_name in handler_names:
            handler = get_handler(handler_name)
            signal.connect(handler)

    print(f"Registered {sum(len(h) for h in SYNCHRONIZATIONS.values())} sync handlers")
```

```python
# main.py - App startup

from fastapi import FastAPI
from crabgrass.syncs import register_all_syncs

app = FastAPI()

@app.on_event("startup")
def startup():
    register_all_syncs()  # Registry drives all wiring
```

**Why this matters:** The registry is now the single source of truth. To add a new sync, you add one line to `SYNCHRONIZATIONS`. To see what happens when an event fires, you read the registry. No hunting through decorators.

### How Concepts Emit Events

Each concept module emits signals when its actions complete. Concepts import signals from the central signals module - they don't define their own.

```python
# concepts/idea.py

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

# Import signals from central location (not defined here!)
from syncs.signals import idea_created, idea_updated

@dataclass
class Idea:
    """
    The Idea concept: a container for strategic responses.

    An Idea groups Summary, Challenge, Approach, and CoherentActions
    into a coherent unit that can be linked to Objectives.
    """
    id: str
    title: str
    status: str  # Draft, Active, Archived
    author_id: str
    created_at: datetime
    updated_at: datetime


class IdeaActions:
    """Actions that can be performed on the Idea concept."""

    def __init__(self, db):
        self.db = db

    def create(self, title: str, author_id: str, summary_content: str) -> Idea:
        """
        Create a new Idea with an initial Summary.

        Emits: idea.created
        Triggers (per registry): find_similar_ideas
        """
        idea_id = str(uuid4())
        idea = Idea(
            id=idea_id,
            title=title,
            status="Draft",
            author_id=author_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Persist to database
        self.db.insert_idea(idea)

        # Create the Summary (which emits its own signal)
        from concepts.summary import SummaryActions
        SummaryActions(self.db).create(idea_id, summary_content)

        # Emit signal - handlers are wired via registry, not here
        idea_created.send(self, idea_id=idea_id, title=title)

        return idea

    def update(self, idea_id: str, **changes) -> Idea:
        """
        Update an existing Idea.

        Emits: idea.updated
        """
        idea = self.db.update_idea(idea_id, **changes)
        idea_updated.send(self, idea_id=idea_id, changes=changes)
        return idea
```

```python
# concepts/summary.py

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from syncs.signals import summary_created, summary_updated

@dataclass
class Summary:
    id: str
    idea_id: str
    content: str
    embedding: list = None  # Populated by sync handler
    created_at: datetime = None
    updated_at: datetime = None


class SummaryActions:
    """Actions for the Summary concept."""

    def __init__(self, db):
        self.db = db

    def create(self, idea_id: str, content: str) -> Summary:
        """
        Create a Summary for an Idea.

        Emits: summary.created
        Triggers (per registry): generate_summary_embedding
        """
        summary_id = str(uuid4())
        summary = Summary(
            id=summary_id,
            idea_id=idea_id,
            content=content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.insert_summary(summary)

        # Emit signal - embedding handler will populate embedding field
        summary_created.send(self, summary_id=summary_id, content=content, idea_id=idea_id)

        return summary

    def update(self, summary_id: str, content: str) -> Summary:
        """
        Update a Summary's content.

        Emits: summary.updated
        Triggers (per registry): generate_summary_embedding, find_similar_ideas
        """
        summary = self.db.update_summary(summary_id, content=content)

        summary_updated.send(
            self,
            summary_id=summary_id,
            content=content,
            idea_id=summary.idea_id
        )

        return summary
```

**Key point:** Concepts only emit signals. They don't know what handlers are attached. The registry controls that. This means you can add new behaviors (like "notify users") without touching concept code.

### Synchronization Flow Diagram

```
User Action                 Concept Action              Synchronizations
───────────────────────────────────────────────────────────────────────────

User types idea      ──►    Idea.create()        ──►    ┌─────────────────────┐
in chat                          │                      │ generate_summary_   │
                                 │                      │ embedding           │
                                 │                      ├─────────────────────┤
                                 │                      │ find_similar_ideas  │──► Returns to agent
                                 ▼                      └─────────────────────┘
                          Summary.create()       ──►    ┌─────────────────────┐
                                                        │ generate_summary_   │
                                                        │ embedding           │
                                                        └─────────────────────┘

User edits Challenge ──►    Challenge.update()   ──►    ┌─────────────────────┐
in canvas                                               │ generate_challenge_ │
                                                        │ embedding           │
                                                        └─────────────────────┘
```

### Future Synchronizations (Post-Demo)

The architecture makes it trivial to add more syncs later:

```python
# Future syncs that plug into the same signals

FUTURE_SYNCHRONIZATIONS = {
    "Idea.create": [
        "add_to_nurture_queue",          # Queue for NurtureAgent
    ],
    "Idea.linkToObjective": [
        "notify_objective_watchers",     # Alert leadership
    ],
    "Challenge.create": [
        "add_to_connection_queue",       # Queue for ConnectionAgent
    ],
    "ConnectionAgent.foundSimilarity": [
        "add_to_surfacing_queue",        # Queue for SurfacingAgent
    ],
}
```

---

## Phase 1: Project Setup

### 1.1 Repository Structure

The backend is organized around **Concepts** and **Synchronizations**, not traditional layers:

```
crabgrass/
├── backend/
│   ├── pyproject.toml          # uv project config
│   ├── src/
│   │   └── crabgrass/
│   │       ├── __init__.py
│   │       ├── main.py         # FastAPI app entry
│   │       ├── config.py       # Settings/env vars
│   │       │
│   │       ├── concepts/           # ◄── CONCEPTS: Self-contained modules
│   │       │   ├── __init__.py
│   │       │   ├── idea.py         # Idea concept (state + actions)
│   │       │   ├── summary.py      # Summary concept
│   │       │   ├── challenge.py    # Challenge concept
│   │       │   ├── approach.py     # Approach concept
│   │       │   ├── coherent_action.py
│   │       │   ├── session.py      # Session concept (agent convos)
│   │       │   └── user.py         # User concept (mock for demo)
│   │       │
│   │       ├── syncs/              # ◄── SYNCHRONIZATIONS: Explicit contracts
│   │       │   ├── __init__.py         # register_all_syncs() wiring
│   │       │   ├── registry.py         # THE source of truth (not docs!)
│   │       │   ├── signals.py          # blinker signal definitions
│   │       │   └── handlers/           # Handler implementations (no decorators)
│   │       │       ├── __init__.py     # HANDLERS dict + get_handler()
│   │       │       ├── embedding.py    # generate_*_embedding handlers
│   │       │       ├── similarity.py   # find_similar_ideas handler
│   │       │       └── logging.py      # log_session_* handlers
│   │       │
│   │       ├── database/
│   │       │   ├── __init__.py
│   │       │   ├── connection.py   # DuckDB connection
│   │       │   ├── schema.py       # Table definitions
│   │       │   └── seed.py         # Demo seed data
│   │       │
│   │       ├── api/                # Thin layer exposing concepts via HTTP
│   │       │   ├── __init__.py
│   │       │   ├── ideas.py        # Ideas REST endpoints
│   │       │   └── agent.py        # Agent chat endpoints
│   │       │
│   │       ├── agents/
│   │       │   ├── __init__.py
│   │       │   └── idea_assistant.py
│   │       │
│   │       └── services/           # Shared services (not concepts)
│   │           ├── __init__.py
│   │           ├── embedding.py    # Gemini embeddings
│   │           └── similarity.py   # Vector similarity queries
│   │
│   └── data/
│       └── crabgrass.duckdb        # Database file
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Home dashboard
│   │   │   └── ideas/
│   │   │       ├── new/
│   │   │       │   └── page.tsx    # Idea creation
│   │   │       └── [id]/
│   │   │           └── page.tsx    # Idea detail
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   └── RoleToggle.tsx
│   │   │   ├── ideas/
│   │   │   │   ├── IdeaCard.tsx
│   │   │   │   ├── IdeaCanvas.tsx
│   │   │   │   └── IdeaChat.tsx
│   │   │   └── chat/
│   │   │       ├── ChatMessage.tsx
│   │   │       └── ChatInput.tsx
│   │   ├── lib/
│   │   │   ├── api.ts              # API client
│   │   │   └── types.ts            # TypeScript types
│   │   └── hooks/
│   │       └── useChat.ts          # AG-UI chat hook
│   └── public/
├── docs/
│   └── (existing docs)
├── .env.example
└── README.md
```

### 1.2 Dependencies

**Backend (pyproject.toml)**
```toml
[project]
name = "crabgrass"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "duckdb>=1.1.0",
    "google-adk>=0.1.0",
    "google-generativeai>=0.8.0",
    "blinker>=1.8.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "httpx>=0.27.0",
]
```

**Frontend (package.json)**
```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@ag-ui-protocol/client": "latest",
    "@ag-ui-protocol/react": "latest"
  }
}
```

### 1.3 Environment Configuration

```bash
# .env
GOOGLE_API_KEY=your-gemini-api-key
DATABASE_PATH=./data/crabgrass.duckdb
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

---

## Phase 2: Database Layer

### 2.1 Schema Design

The demo uses a simplified schema focused on Ideas.

```sql
-- Users table (mock users for demo)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('Frontline', 'Senior')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ideas table
CREATE TABLE IF NOT EXISTS ideas (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Active', 'Archived')),
    author_id VARCHAR NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Summaries table (one per Idea)
CREATE TABLE IF NOT EXISTS summaries (
    id VARCHAR PRIMARY KEY,
    idea_id VARCHAR NOT NULL UNIQUE REFERENCES ideas(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding FLOAT[768],  -- Gemini embedding dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Challenges table (can be shared, but simplified for demo)
CREATE TABLE IF NOT EXISTS challenges (
    id VARCHAR PRIMARY KEY,
    idea_id VARCHAR NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding FLOAT[768],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Approaches table
CREATE TABLE IF NOT EXISTS approaches (
    id VARCHAR PRIMARY KEY,
    idea_id VARCHAR NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding FLOAT[768],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coherent Actions table
CREATE TABLE IF NOT EXISTS coherent_actions (
    id VARCHAR PRIMARY KEY,
    idea_id VARCHAR NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'In Progress', 'Complete')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table (agent conversations)
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    idea_id VARCHAR REFERENCES ideas(id) ON DELETE SET NULL,
    status VARCHAR NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Archived')),
    messages JSON,  -- Array of {role, content, timestamp}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 Vector Similarity Index

```sql
-- Install VSS extension
INSTALL vss;
LOAD vss;

-- Create HNSW index for similarity search
CREATE INDEX IF NOT EXISTS summaries_embedding_idx
ON summaries USING HNSW (embedding)
WITH (metric = 'cosine');

CREATE INDEX IF NOT EXISTS challenges_embedding_idx
ON challenges USING HNSW (embedding)
WITH (metric = 'cosine');

CREATE INDEX IF NOT EXISTS approaches_embedding_idx
ON approaches USING HNSW (embedding)
WITH (metric = 'cosine');
```

### 2.3 Seed Data

Pre-populate with 3-4 sample Ideas to demonstrate similarity search:

| Idea | Summary | Challenge | Approach |
|------|---------|-----------|----------|
| Japan Partnership Strategy | Explore reseller partnerships to enter Japan market | No established presence in Japan despite 15% market growth | Leverage existing APAC reseller network |
| ERP Integration Concept | Customers waste hours on manual data reconciliation | Customers spend 10+ hours/week on data sync | Build native ERP integration connectors |
| Customer Feedback Loop | Need systematic way to capture customer insights | Valuable feedback scattered across channels | Implement unified feedback collection system |

---

## Phase 3: Backend API

### 3.1 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ideas` | List all ideas (with filters) |
| POST | `/api/ideas` | Create new idea |
| GET | `/api/ideas/{id}` | Get idea with full details |
| PATCH | `/api/ideas/{id}` | Update idea |
| DELETE | `/api/ideas/{id}` | Delete idea |
| GET | `/api/ideas/{id}/similar` | Find similar ideas |
| POST | `/api/agent/chat` | Send message to IdeaAssistantAgent |
| GET | `/api/agent/chat/{session_id}` | Get session history |

### 3.2 Pydantic Models

```python
# models/idea.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SummaryCreate(BaseModel):
    content: str

class SummaryResponse(BaseModel):
    id: str
    content: str
    created_at: datetime
    updated_at: datetime

class ChallengeCreate(BaseModel):
    content: str

class ChallengeResponse(BaseModel):
    id: str
    content: str
    created_at: datetime
    updated_at: datetime

class ApproachCreate(BaseModel):
    content: str

class ApproachResponse(BaseModel):
    id: str
    content: str
    created_at: datetime
    updated_at: datetime

class CoherentActionCreate(BaseModel):
    content: str
    status: str = "Pending"

class CoherentActionResponse(BaseModel):
    id: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime

class IdeaCreate(BaseModel):
    title: str
    summary: SummaryCreate

class IdeaUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[SummaryCreate] = None
    challenge: Optional[ChallengeCreate] = None
    approach: Optional[ApproachCreate] = None

class IdeaListItem(BaseModel):
    id: str
    title: str
    status: str
    author_name: str
    created_at: datetime
    summary_preview: str  # First 100 chars

class IdeaDetail(BaseModel):
    id: str
    title: str
    status: str
    author_id: str
    author_name: str
    created_at: datetime
    updated_at: datetime
    summary: Optional[SummaryResponse]
    challenge: Optional[ChallengeResponse]
    approach: Optional[ApproachResponse]
    coherent_actions: List[CoherentActionResponse]

class SimilarIdea(BaseModel):
    id: str
    title: str
    similarity_score: float
    match_type: str  # "summary", "challenge", "approach"
```

### 3.3 IdeaAssistantAgent

The agent helps users create and refine Ideas through conversation. Built with Google ADK.

**Agent Responsibilities:**
1. Greet user and ask about their idea
2. Help articulate a clear Summary
3. Guide toward defining a Challenge (optional)
4. Suggest an Approach (optional)
5. Propose Coherent Actions (optional)
6. Save/update the Idea in the database

**Agent System Prompt:**
```
You are the IdeaAssistant, helping users capture and structure their ideas in Crabgrass.

Your role is to:
1. Listen to the user's initial thought or hunch
2. Help them articulate it as a clear Summary
3. Gently guide them toward defining a Challenge (the problem they're addressing)
4. Suggest an Approach (a guiding policy for addressing the Challenge)
5. Propose Coherent Actions (specific steps to implement the Approach)

Guidelines:
- Start conversationally. Don't force structure immediately.
- Accept that users may only have a rough hunch - that's okay.
- When you identify something that sounds like a Challenge, point it out.
- Offer to help at each step, but don't pressure.
- Be concise - this is a work tool, not a chatbot.
- When the user seems satisfied, confirm the structured idea.

You have access to the following tools:
- save_idea: Save or update the current idea
- find_similar: Find ideas similar to the current content

Current idea context will be provided with each message.
```

**Agent Tools:**

```python
@tool
def save_idea(
    title: str,
    summary: str,
    challenge: Optional[str] = None,
    approach: Optional[str] = None,
    actions: Optional[List[str]] = None
) -> dict:
    """Save or update the idea being worked on."""
    pass

@tool
def find_similar(content: str, content_type: str = "summary") -> List[dict]:
    """Find ideas with similar content.

    Args:
        content: The text to find similarities for
        content_type: One of "summary", "challenge", or "approach"

    Returns:
        List of similar ideas with titles and similarity scores
    """
    pass
```

### 3.4 Embedding Service

```python
# services/embedding.py
import google.generativeai as genai
from typing import List

class EmbeddingService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = "models/text-embedding-004"

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="semantic_similarity"
        )
        return result['embedding']

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        results = []
        for text in texts:
            results.append(self.embed(text))
        return results
```

### 3.5 Similarity Service

```python
# services/similarity.py
from typing import List, Tuple
import duckdb

class SimilarityService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def find_similar_summaries(
        self,
        embedding: List[float],
        limit: int = 5,
        exclude_idea_id: str = None
    ) -> List[Tuple[str, str, float]]:
        """Find ideas with similar summaries.

        Returns list of (idea_id, title, similarity_score)
        """
        conn = duckdb.connect(self.db_path, read_only=True)

        query = """
        SELECT
            i.id,
            i.title,
            1 - array_cosine_distance(s.embedding, $1::FLOAT[768]) as similarity
        FROM summaries s
        JOIN ideas i ON s.idea_id = i.id
        WHERE s.embedding IS NOT NULL
        """

        if exclude_idea_id:
            query += f" AND i.id != '{exclude_idea_id}'"

        query += """
        ORDER BY similarity DESC
        LIMIT $2
        """

        results = conn.execute(query, [embedding, limit]).fetchall()
        conn.close()
        return results
```

---

## Phase 4: Frontend

### 4.1 Home Dashboard

**Route:** `/`

**Components:**
- `Header` - Logo, role toggle
- `RoleToggle` - Switch between Frontline/Senior (mock, stored in localStorage)
- `IdeaList` - Scrollable list of idea cards
- `NewIdeaButton` - Navigates to `/ideas/new`

**Data fetching:**
- GET `/api/ideas` on mount
- Refresh on focus/visibility change

**Wireframe mapping:**
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🦀 CRABGRASS                                   [ Sarah ◉ │ ○ VP Sales ]     │
│                                                  Frontline    Senior         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [+ New Idea]                                                                │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  YOUR IDEAS                                                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────────────────┐   │
│ │ Japan Partnership Strategy                                              │   │
│ │ Draft · Sarah · 2h ago                                                  │   │
│ │ "Explore reseller partnerships to enter Japan market..."               │   │
│ └────────────────────────────────────────────────────────────────────────┘   │
│ ┌────────────────────────────────────────────────────────────────────────┐   │
│ │ ERP Integration Concept                                                 │   │
│ │ Active · Sarah · 1d ago                                                 │   │
│ │ "Customers waste hours on manual data reconciliation..."              │   │
│ └────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Idea Creation Screen

**Route:** `/ideas/new`

**Components:**
- `Header` - With back button
- `ChatInterface` - Full-screen chat with IdeaAssistantAgent
- `ChatMessage` - Individual message bubbles
- `ChatInput` - Text input with send button
- Action buttons: "Save as Draft", "Continue to Edit"

**AG-UI Integration:**
- Use `@ag-ui-protocol/react` for streaming responses
- SSE connection to `/api/agent/chat`
- Real-time message rendering

**Flow:**
1. User starts conversation with agent
2. Agent guides toward articulating idea
3. "Save as Draft" creates idea, returns to dashboard
4. "Continue" creates idea, navigates to detail screen

### 4.3 Idea Detail Screen

**Route:** `/ideas/[id]`

**Components:**
- `Header` - With back button, status badge
- `IdeaCanvas` (70%) - Structured editing sections
  - `SummarySection` - Editable summary field
  - `ChallengeSection` - Optional, with placeholder
  - `ApproachSection` - Optional, with placeholder
  - `ActionsSection` - List of coherent actions
- `IdeaChat` (30%) - Sidebar chat with agent
- `SimilarIdeas` - Collapsible panel showing similar ideas

**Canvas Sections:**
Each section has:
- Edit mode toggle
- Auto-save on blur
- Visual indicator when AI suggests content

**AG-UI Integration:**
- Bidirectional sync: user edits visible to agent, agent suggestions appear in canvas
- Agent can propose edits that show as "pending suggestions"
- User accepts/rejects/modifies suggestions

### 4.4 Shared Components

```typescript
// components/layout/Header.tsx
interface HeaderProps {
  title?: string;
  showBack?: boolean;
  status?: 'Draft' | 'Active' | 'Archived';
}

// components/layout/RoleToggle.tsx
// Switches between 'Frontline' and 'Senior'
// Stores preference in localStorage
// For demo: purely cosmetic (no functional difference in v1)

// components/ideas/IdeaCard.tsx
interface IdeaCardProps {
  id: string;
  title: string;
  status: string;
  authorName: string;
  createdAt: Date;
  summaryPreview: string;
  onClick: () => void;
}

// components/chat/ChatMessage.tsx
interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

// components/chat/ChatInput.tsx
interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

---

## Phase 5: AG-UI Protocol Integration

### 5.1 Backend Events

The backend should emit AG-UI protocol events for:

1. **Text Deltas** - Streaming agent responses
2. **Tool Calls** - When agent uses save_idea or find_similar
3. **State Updates** - When idea structure changes

```python
# Example SSE event format
{
    "type": "text_delta",
    "data": {
        "delta": "That's a great observation! "
    }
}

{
    "type": "tool_call",
    "data": {
        "name": "find_similar",
        "arguments": {"content": "ERP integration", "content_type": "summary"},
        "result": [{"id": "idea-2", "title": "ERP Integration Concept", "score": 0.89}]
    }
}

{
    "type": "state_update",
    "data": {
        "idea": {
            "title": "Customer Data Sync Solution",
            "summary": "..."
        }
    }
}
```

### 5.2 Frontend Consumption

```typescript
// hooks/useChat.ts
import { useAgentStream } from '@ag-ui-protocol/react';

export function useChat(sessionId: string) {
  const { messages, sendMessage, isStreaming, state } = useAgentStream({
    url: `/api/agent/chat/${sessionId}`,
    onStateUpdate: (state) => {
      // Handle idea updates from agent
    },
    onToolCall: (toolCall) => {
      // Handle tool call results (e.g., show similar ideas)
    }
  });

  return { messages, sendMessage, isStreaming, state };
}
```

---

## Phase 6: Implementation Order

### Step 1: Backend Foundation
1. Initialize uv project with dependencies
2. Create DuckDB connection module
3. Define and create schema (tables for each concept)
4. Create basic FastAPI app with health check

### Step 2: Concepts Layer
Build each concept as a self-contained module:

1. **User concept** (`concepts/user.py`)
   - Mock users for demo (Sarah, VP Sales)
   - Actions: get_by_id, get_current (returns mock user)

2. **Idea concept** (`concepts/idea.py`)
   - State: id, title, status, author_id, timestamps
   - Actions: create, update, archive, delete, get_by_id, list_all
   - Emits: `idea.created`, `idea.updated`, `idea.archived`

3. **Summary concept** (`concepts/summary.py`)
   - State: id, idea_id, content, embedding
   - Actions: create, update, get_by_idea_id
   - Emits: `summary.created`, `summary.updated`

4. **Challenge concept** (`concepts/challenge.py`)
   - State: id, idea_id, content, embedding
   - Actions: create, update, delete, get_by_idea_id
   - Emits: `challenge.created`, `challenge.updated`

5. **Approach concept** (`concepts/approach.py`)
   - State: id, idea_id, content, embedding
   - Actions: create, update, delete, get_by_idea_id
   - Emits: `approach.created`, `approach.updated`

6. **CoherentAction concept** (`concepts/coherent_action.py`)
   - State: id, idea_id, content, status
   - Actions: create, update, complete, delete, list_by_idea_id
   - Emits: `action.created`, `action.completed`

7. **Session concept** (`concepts/session.py`)
   - State: id, user_id, idea_id, messages, status
   - Actions: start, add_message, end, get_by_id
   - Emits: `session.started`, `session.ended`

### Step 3: Signals & Synchronizations
Build the sync infrastructure with registry as single source of truth:

1. **Define signals** (`syncs/signals.py`)
   - Create blinker Namespace for all signals
   - Implement `get_signal(name)` for dynamic lookup
   - Pre-define signals for type hints

2. **Sync registry** (`syncs/registry.py`)
   - **THE source of truth** - not documentation
   - Declarative mapping: event name → list of handler names
   - Changing this file changes system behavior

3. **Handler registry** (`syncs/handlers/__init__.py`)
   - `HANDLERS` dict mapping names to functions
   - `get_handler(name)` for lookup
   - Handlers have no decorators - just plain functions

4. **Embedding handlers** (`syncs/handlers/embedding.py`)
   - `generate_summary_embedding(sender, summary_id, content, **kwargs)`
   - `generate_challenge_embedding(sender, challenge_id, content, **kwargs)`
   - `generate_approach_embedding(sender, approach_id, content, **kwargs)`

5. **Similarity handlers** (`syncs/handlers/similarity.py`)
   - `find_similar_ideas(sender, idea_id, **kwargs)`

6. **Wiring function** (`syncs/__init__.py`)
   - `register_all_syncs()`: reads registry, wires handlers to signals
   - Called once at app startup
   - Logs number of handlers registered

### Step 4: Services Layer
Shared utilities used by sync handlers:

1. **EmbeddingService** (`services/embedding.py`)
   - `embed(text)`: Generate embedding via Gemini
   - `embed_batch(texts)`: Batch embeddings

2. **SimilarityService** (`services/similarity.py`)
   - `find_similar_summaries(embedding, limit)`: VSS query
   - `find_similar_challenges(embedding, limit)`: VSS query
   - `find_similar_approaches(embedding, limit)`: VSS query

### Step 5: Seed Data
1. Create demo users (Sarah - Frontline, VP Sales - Senior)
2. Create 3-4 sample ideas with full structure
3. Generate embeddings for all content
4. Verify similarity search works

### Step 6: API Layer
Thin HTTP layer that delegates to concepts:

1. **Ideas API** (`api/ideas.py`)
   - GET `/api/ideas` → `Idea.list_all()`
   - POST `/api/ideas` → `Idea.create()` (triggers syncs)
   - GET `/api/ideas/{id}` → `Idea.get_by_id()` + related concepts
   - PATCH `/api/ideas/{id}` → `Idea.update()` (triggers syncs)
   - GET `/api/ideas/{id}/similar` → query similarity service

2. **Agent API** (`api/agent.py`)
   - POST `/api/agent/chat` → Start/continue session, stream response
   - GET `/api/agent/chat/{session_id}` → Get session history

### Step 7: IdeaAssistantAgent
1. Set up Google ADK
2. Define agent with system prompt
3. Implement `save_idea` tool (calls concept actions)
4. Implement `find_similar` tool (calls similarity service)
5. Create SSE streaming endpoint

### Step 8: Frontend Foundation
1. Initialize Next.js project
2. Create layout with header
3. Implement RoleToggle (localStorage)
4. Create API client utilities

### Step 9: Home Dashboard
1. Build IdeaCard component
2. Build IdeaList component
3. Fetch and display ideas
4. Add "New Idea" button

### Step 10: Idea Creation Screen
1. Build ChatMessage component
2. Build ChatInput component
3. Build ChatInterface with AG-UI
4. Implement SSE streaming
5. Add "Save as Draft" / "Continue" actions

### Step 11: Idea Detail Screen
1. Build canvas section components
2. Build inline editing
3. Build chat sidebar
4. Implement AG-UI state sync
5. Build similar ideas panel

### Step 12: Integration Testing
1. Test sync contracts fire correctly
2. Test embedding generation on create/update
3. Test similarity search returns expected results
4. Test agent conversation flow end-to-end
5. Add error handling and loading states

---

## Demo Scenarios

The following scenarios should work end-to-end:

### Scenario 1: Capture a Hunch
1. User clicks "New Idea"
2. Types: "I heard from a customer that they struggle with our reporting tools"
3. Agent helps articulate this as a Summary
4. User saves as Draft
5. Idea appears on dashboard

### Scenario 2: Structure an Idea
1. User opens an existing idea
2. Chats with agent to define Challenge
3. Agent suggests Challenge text, user accepts
4. Challenge appears in canvas
5. Agent suggests Approach
6. User modifies and accepts

### Scenario 3: Discover Similar Ideas
1. User creates idea about "data synchronization"
2. Agent finds similar "ERP Integration Concept"
3. User sees similarity notification
4. User can click to view related idea

---

## Testing Synchronization Contracts

The truly declarative architecture enables multiple levels of testing:

### 1. Test the Registry Itself

Verify the registry declares the expected contracts:

```python
# tests/test_registry.py

from crabgrass.syncs.registry import SYNCHRONIZATIONS

class TestRegistryContracts:
    """Verify the registry declares expected contracts."""

    def test_summary_created_triggers_embedding(self):
        """Contract: summary.created → generate_summary_embedding"""
        assert "generate_summary_embedding" in SYNCHRONIZATIONS["summary.created"]

    def test_summary_updated_triggers_embedding_and_similarity(self):
        """Contract: summary.updated → embedding + similarity"""
        handlers = SYNCHRONIZATIONS["summary.updated"]
        assert "generate_summary_embedding" in handlers
        assert "find_similar_ideas" in handlers

    def test_idea_created_triggers_similarity(self):
        """Contract: idea.created → find_similar_ideas"""
        assert "find_similar_ideas" in SYNCHRONIZATIONS["idea.created"]

    def test_all_handlers_exist(self):
        """Every handler in registry must be implemented."""
        from crabgrass.syncs.handlers import HANDLERS

        for event, handler_names in SYNCHRONIZATIONS.items():
            for handler_name in handler_names:
                assert handler_name in HANDLERS, \
                    f"Handler '{handler_name}' for '{event}' not implemented"
```

### 2. Test Handler Behavior

Test that handlers do what they claim:

```python
# tests/test_handlers.py

import pytest
from unittest.mock import patch, MagicMock
from crabgrass.syncs.handlers.embedding import generate_summary_embedding
from crabgrass.syncs.handlers.similarity import find_similar_ideas

class TestEmbeddingHandlers:
    """Test handler implementations."""

    def test_generate_summary_embedding_calls_service(self):
        with patch('crabgrass.syncs.handlers.embedding.EmbeddingService') as mock_svc:
            with patch('crabgrass.syncs.handlers.embedding.get_db') as mock_db:
                mock_svc.return_value.embed.return_value = [0.1] * 768

                generate_summary_embedding(
                    sender=None,
                    summary_id="sum-123",
                    content="Test content"
                )

                mock_svc.return_value.embed.assert_called_once_with("Test content")
                mock_db.return_value.execute.assert_called_once()
```

### 3. Test Wiring Works End-to-End

Test that emitting a signal triggers the registered handlers:

```python
# tests/test_wiring.py

import pytest
from unittest.mock import patch
from crabgrass.syncs import register_all_syncs
from crabgrass.syncs.signals import summary_created

class TestSyncWiring:
    """Test that registry wiring actually works."""

    @pytest.fixture(autouse=True)
    def setup_syncs(self):
        """Register all syncs before each test."""
        register_all_syncs()

    def test_summary_created_triggers_embedding_handler(self):
        """End-to-end: signal → registry → handler."""
        with patch('crabgrass.syncs.handlers.embedding.EmbeddingService') as mock_svc:
            with patch('crabgrass.syncs.handlers.embedding.get_db'):
                mock_svc.return_value.embed.return_value = [0.1] * 768

                # Emit signal (like a concept would)
                summary_created.send(
                    None,
                    summary_id="sum-123",
                    content="Test summary",
                    idea_id="idea-456"
                )

                # Handler was called because registry wired it
                mock_svc.return_value.embed.assert_called_once()
```

### Sync Verification Checklist

| Sync Contract | Trigger | Handler | Test |
|--------------|---------|---------|------|
| Summary → Embedding | `summary.created` | `generate_summary_embedding` | ✓ |
| Summary → Embedding | `summary.updated` | `generate_summary_embedding` | ✓ |
| Challenge → Embedding | `challenge.created` | `generate_challenge_embedding` | ✓ |
| Challenge → Embedding | `challenge.updated` | `generate_challenge_embedding` | ✓ |
| Approach → Embedding | `approach.created` | `generate_approach_embedding` | ✓ |
| Approach → Embedding | `approach.updated` | `generate_approach_embedding` | ✓ |
| Idea → Similarity | `idea.created` | `find_similar_ideas` | ✓ |
| Summary → Similarity | `summary.updated` | `find_similar_ideas` | ✓ |

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| Ideas persist across restarts | Create idea, restart server, idea still visible |
| Agent conversations work | Full back-and-forth dialogue with streaming |
| Similarity search functional | Creating new idea surfaces related existing ideas |
| Canvas editing works | Can edit Summary, Challenge, Approach inline |
| Role toggle works | Toggle state persists in localStorage |
| Responsive layout | Works on desktop (1280px+) |
| **Sync contracts verified** | All sync tests pass (embedding + similarity) |
| **Concepts emit signals** | Creating/updating concepts triggers handlers |

---

## Future Enhancements (Post-Demo)

After v1, the following can be added incrementally:

1. **Objectives** - Add Objective screens and linking
2. **Background Agents** - ConnectionAgent, NurtureAgent, SurfacingAgent
3. **Notifications** - Real-time alerts column
4. **Multi-user** - Multiple mock users with switching
5. **Graph Relationships** - DuckPGQ for relationship queries
6. **Comments** - Collaboration on ideas
