# Customer Journey Mapper — Architecture

## Overview

A modular backend for mapping customer journeys as hierarchical graphs, ingesting structured/unstructured data, defining product goals, and surfacing a "Sonar" focus map showing where to invest effort.

**Stack**: Python 3.12, FastAPI, PostgreSQL 16, SQLAlchemy 2.0, Alembic, Pydantic v2

## Modules

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  Workspace   │◄────│   Journey    │◄────│    Goals     │
│  (auth/      │     │   Engine     │     │   Engine     │
│   tenancy)   │     │  (graph)     │     │  (KPIs)      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                     │
       │              ┌─────▼───────┐       ┌─────▼───────┐
       │              │   Mapping    │──────►│    Sonar    │
       │              │   Engine     │       │   Engine    │
       │              └─────▲───────┘       │  (scoring)  │
       │                    │               └─────────────┘
       │              ┌─────┴───────┐
       └─────────────►│  Ingestion   │
                      │  Pipeline    │
                      └──────────────┘
```

### 1. Workspace (`app/workspace/`)
Multi-tenancy boundaries and API key authentication. Every entity in the system belongs to a workspace.

### 2. Journey Engine (`app/journey/`)
Cascading directed graph of Nodes and Edges. Nodes have types (JOURNEY_ROOT, STAGE, TOUCHPOINT, MICRO_ACTION) and can contain sub-journeys via `parent_node_id`. Supports recursive CTE traversal and DFS cycle detection.

### 3. Data Ingestion (`app/ingestion/`)
Three-stage pipeline: raw capture → rule-based normalization (JSONPath) → NLP classification (pluggable). Emits `ingestion.event.normalized` events.

### 4. Mapping Engine (`app/mapping/`)
Declarative rules map normalized events to journey nodes, producing MappedSignals (POSITIVE/NEGATIVE/NEUTRAL). Falls back to auto-mapping via input_schema matching.

### 5. Goal Engine (`app/goals/`)
Product goals/KPIs attached to journey nodes. Periodic snapshot computation measures current_value against target_value.

### 6. Sonar Engine (`app/sonar/`)
Scores each node on Health (signal ratio), Opportunity (goal gaps), Urgency (trend + impact), and Composite (weighted combination). Scores cascade up the tree. Produces a ranked focus map.

## Data Flow

```
External Source → Ingestion (normalize/classify)
  → event: ingestion.event.normalized
    → Mapping (evaluate rules → MappedSignals)
      → event: mapping.signal.created
        → Sonar (compute scores → cascade → focus map)

Goal Engine (periodic) → snapshots → feeds Sonar opportunity/urgency scores
```

## Communication Patterns

| Pattern | Usage |
|---------|-------|
| Sync service calls | In-process module-to-module calls (monolith-first) |
| Async event bus | `app/events.py` — ingestion→mapping→sonar pipeline |
| No cross-schema DB | Each module owns its PostgreSQL schema |

## Database

Single PostgreSQL instance, 6 schemas: `workspace`, `journey`, `ingestion`, `mapping`, `goals`, `sonar`. Cross-module references are UUID values validated at the application layer.

## Running

```bash
docker-compose up -d db           # Start PostgreSQL
pip install -e ".[dev]"           # Install dependencies
alembic upgrade head              # Run migrations
uvicorn app.main:app --reload     # Start dev server on :8000
pytest                            # Run tests
```
