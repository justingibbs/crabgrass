# Project Conventions

This document defines the development conventions for Crabgrass.

---

## Package Management (uv)

We use [uv](https://github.com/astral-sh/uv) for Python package and project management.

### Adding Dependencies

```bash
# Add a production dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Add with version constraint
uv add "fastapi>=0.115.0"
```

### Running Commands

```bash
# Run the backend server
uv run uvicorn crabgrass.main:app --reload

# Run Python scripts
uv run python script.py

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=crabgrass
```

### Syncing Environment

```bash
# Install all dependencies from pyproject.toml
uv sync

# Install including dev dependencies
uv sync --dev
```

---

## Project Structure

### Backend Organization

The backend follows **Concepts and Synchronizations** architecture (see `concepts-synchronizations.md`):

```
backend/src/crabgrass/
├── concepts/       # Self-contained domain modules
├── syncs/          # Declarative synchronization contracts
├── api/            # Thin HTTP layer (delegates to concepts)
├── agents/         # AI agent definitions
├── services/       # Shared utilities (embedding, similarity)
└── database/       # DuckDB connection and schema
```

**Key principle:** Business logic lives in concepts. API endpoints are thin wrappers.

### Frontend Organization

```
frontend/src/
├── app/            # Next.js App Router pages
├── components/     # React components
├── lib/            # Utilities and API client
└── hooks/          # Custom React hooks
```

---

## Concepts

Each concept is a self-contained module with:

1. **State** - A dataclass defining the concept's data
2. **Actions** - A class with methods that operate on the concept
3. **Signals** - Events emitted when actions complete

```python
# concepts/example.py

from dataclasses import dataclass
from syncs.signals import example_created

@dataclass
class Example:
    id: str
    name: str

class ExampleActions:
    def __init__(self, db):
        self.db = db

    def create(self, name: str) -> Example:
        example = Example(id=generate_id(), name=name)
        self.db.insert_example(example)
        example_created.send(self, example_id=example.id, name=name)
        return example
```

**Concepts do NOT:**
- Know about HTTP/API layer
- Know what handlers are attached to their signals
- Import from other concepts (use signals for cross-concept communication)

---

## Synchronizations

Synchronizations are explicit contracts defining what happens when concept events fire.

### The Registry is the Source of Truth

```python
# syncs/registry.py - Changing this changes behavior

SYNCHRONIZATIONS = {
    "example.created": ["handler_a", "handler_b"],
}
```

### Handlers are Plain Functions

```python
# syncs/handlers/example.py - No decorators!

def handler_a(sender, example_id: str, **kwargs):
    # Do something
    pass
```

### Wiring Happens at Startup

```python
# syncs/__init__.py
def register_all_syncs():
    for event, handlers in SYNCHRONIZATIONS.items():
        signal = get_signal(event)
        for handler_name in handlers:
            signal.connect(get_handler(handler_name))
```

**To add new behavior:** Add one line to the registry. Don't modify concept code.

---

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_syncs.py

# With verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x
```

### Test Organization

```
backend/tests/
├── test_registry.py    # Verify sync contracts are declared
├── test_handlers.py    # Test handler behavior in isolation
├── test_wiring.py      # Test signal → handler wiring
├── test_concepts/      # Test concept actions
└── test_api/           # Test API endpoints
```

### Testing Sync Contracts

1. **Test the registry** - Verify expected contracts are declared
2. **Test handlers** - Verify handlers do what they claim
3. **Test wiring** - Verify signals trigger registered handlers

---

## Code Style

### Python

- Use type hints for function signatures
- Use dataclasses for concept state
- Docstrings for public functions (brief, focus on what not how)
- No decorators on sync handlers (wiring is declarative)

### TypeScript

- Use TypeScript strict mode
- Define interfaces for component props
- Use React hooks for state management

### General

- Keep functions small and focused
- Prefer explicit over implicit
- Comments explain "why", code explains "what"

---

## Git Conventions

### Commit Messages

Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `docs`: Documentation only
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat: add Summary concept with embedding sync
fix: handle missing embedding in similarity search
refactor: extract handler registry to separate module
```

### Branches

- `main` - Production-ready code
- `feat/<name>` - Feature branches
- `fix/<name>` - Bug fix branches

---

## Environment Variables

Required:
```bash
GOOGLE_API_KEY=your-gemini-api-key
```

Optional:
```bash
DATABASE_PATH=./data/crabgrass.duckdb  # Default location
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

---

## Common Tasks

### Start Development

```bash
# Backend
cd backend
uv sync --dev
uv run uvicorn crabgrass.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Add a New Concept

1. Create `concepts/<name>.py` with state dataclass and actions class
2. Add signals to `syncs/signals.py`
3. Add any sync handlers to `syncs/handlers/`
4. Register handlers in `syncs/handlers/__init__.py`
5. Add contracts to `syncs/registry.py`
6. Add API endpoints to `api/` if needed

### Add a New Sync Handler

1. Create handler function in `syncs/handlers/<category>.py`
2. Add to `HANDLERS` dict in `syncs/handlers/__init__.py`
3. Add contract to `syncs/registry.py`

That's it. No decorator wiring needed.
