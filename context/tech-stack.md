# Technology Stack

## Overview

This document outlines the core technologies powering our application, built around a modern Python + Next.js architecture with AI agent capabilities. The demo uses DuckDB as an embedded database with graph and vector extensions.

---

## Frontend

| Technology | Purpose |
|------------|---------|
| **Next.js** | React framework for server-side rendering, routing, and frontend architecture |
| **AG-UI** | Agent-user interface protocol for seamless human-agent interaction ([ag-ui-protocol](https://github.com/ag-ui-protocol/ag-ui)) |

---

## Backend

| Technology | Purpose |
|------------|---------|
| **Python** | Core backend language for business logic and agent development |
| **FastAPI** | Async web framework for REST APIs (used by Google ADK under the hood) |
| **Google ADK** | Agent Development Kit for building, orchestrating, and deploying AI agents |

---

## Event Handling

| Technology | Purpose |
|------------|---------|
| **blinker** | Lightweight in-process signal/event library for decoupled synchronizations |

Blinker enables the [Concept and Synchronization](#concept-and-synchronization) pattern by dispatching events when concepts change, allowing sync handlers to react without tight coupling.

---

## AI / LLM

| Technology | Purpose |
|------------|---------|
| **Gemini** | Google's LLM for agent reasoning, analysis, and conversation |
| **gemini-embedding-001** | Embedding model for vector similarity search (finding similar Ideas, Challenges, Approaches) |

---

## Data & Infrastructure

| Technology | Purpose |
|------------|---------|
| **DuckDB** | Embedded analytical database, single-file persistence for local demo |
| **DuckPGQ** | DuckDB extension for property graph queries (SQL/PGQ) — handles concept relationships |
| **VSS** | DuckDB extension for vector similarity search — HNSW indexing for embedding-based similarity |

### Why DuckDB for the Demo

- **Single-user local demo**: No need for cloud infrastructure or authentication
- **Embedded**: Runs in-process with Python, no separate database server
- **Graph + Vector in one**: DuckPGQ and VSS extensions provide both graph traversal and similarity search
- **Simple persistence**: Everything in one `.duckdb` file

---

## Development Tooling

| Technology | Purpose |
|------------|---------|
| **uv** | Fast Python package and project manager for dependency resolution and virtual environments |

---

## Design Methodology

### Concept and Synchronization

We follow the **Concept and Synchronization** model for software design, as proposed by MIT researchers. This approach emphasizes:

- **Concepts**: Independent, reusable units of functionality with well-defined purposes
- **Synchronization**: Explicit coordination between concepts to compose larger features
- **Legibility**: Clear separation of concerns that makes code easier to understand and maintain
- **Modularity**: Components that can be developed, tested, and reasoned about in isolation

> Reference: [MIT News — New Model for Legible, Modular Software](https://news.mit.edu/2025/mit-researchers-propose-new-model-for-legible-modular-software-1106)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│                    Next.js + AG-UI                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend / Agents                        │
│              FastAPI + Python + Google ADK                  │
│                          │                                  │
│            ┌─────────────┼─────────────┐                    │
│            │             │             │                    │
│         Gemini       blinker       Agents                   │
│    (LLM + Embeddings) (Events)  (ADK-based)                 │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data & Infrastructure                     │
│                        DuckDB                               │
│         ┌──────────────┼──────────────┐                     │
│         │              │              │                     │
│    Concept Tables   DuckPGQ        VSS                      │
│    (Ideas, etc.)   (Graph)    (Vectors)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Configuration

The application requires the following environment variables (see `.env.example`):

```
GOOGLE_API_KEY=your-gemini-api-key
```
