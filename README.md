# Journey Sonar

A modular backend engine for mapping, scoring, and optimizing customer journeys. Build hierarchical customer journey maps, ingest structured and unstructured data from any source, define product goals, and let the Sonar engine tell you exactly where to double down.

---

## What It Does

| Capability | Description |
|---|---|
| **Journey Builder** | Model customer journeys as cascading, hierarchical directed graphs. Every stage can contain sub-stages — drill from "Onboarding" down to "Connect Database" to "Configure SSL". |
| **Data Ingestion** | Pipe in data from webhooks, SDK events, file uploads, or API polls. Structured events and unstructured text (support tickets, chat logs) are both supported. |
| **Mapping Engine** | Declarative rules connect incoming events to journey nodes with a positive, negative, or neutral signal. Auto-mapping suggests connections using input schema matching. |
| **Goal Engine** | Attach KPIs to any node — conversion rate, throughput, time-to-complete, drop-off rate. Goals track their own performance over time via snapshots. |
| **Sonar** | Scores every node on Health, Opportunity, Urgency, and a Composite. Scores cascade up the tree. The focus map ranks where to invest effort right now. |

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  Workspace  │◄────│   Journey   │◄────│    Goals     │
│  (auth /    │     │   Engine    │     │   Engine     │
│  tenancy)   │     │  (graph)    │     │  (KPIs)      │
└──────┬──────┘     └──────┬──────┘     └──────┬───────┘
       │                   │                    │
       │             ┌─────▼──────┐       ┌─────▼───────┐
       │             │  Mapping   │──────►│    Sonar    │
       │             │  Engine    │       │   Engine    │
       │             └─────▲──────┘       │  (scoring)  │
       │                   │              └─────────────┘
       │             ┌─────┴──────┐
       └────────────►│ Ingestion  │
                     │ Pipeline   │
                     └────────────┘
```

The system is built as a **monolith-first** application with strict module boundaries:
- Each of the 6 modules owns its own PostgreSQL schema (`workspace`, `journey`, `ingestion`, `mapping`, `goals`, `sonar`)
- Modules communicate via in-process service interfaces (sync) or an async event bus (fire-and-forget pipeline flows)
- No cross-schema DB queries — cross-module data goes through service interfaces only
- The architecture is designed so any module can be extracted to a microservice later without changing the application layer

Full architecture details: [`ARCHITECTURE.md`](./ARCHITECTURE.md)

---

## Project Structure

```
.
├── app/
│   ├── main.py                     # FastAPI app factory, router registration, event wiring
│   ├── config.py                   # Settings (env-based via pydantic-settings)
│   ├── database.py                 # SQLAlchemy async engine + session factory
│   ├── events.py                   # In-process async event bus
│   ├── common/
│   │   ├── types.py                # All shared enums (NodeType, SignalType, GoalType, …)
│   │   ├── schemas.py              # Shared Pydantic models (Pagination, WorkspaceContext, …)
│   │   └── exceptions.py          # Shared exception hierarchy
│   ├── middleware/
│   │   ├── workspace_context.py    # API key resolution per request
│   │   └── error_handling.py      # Global exception handlers
│   │
│   ├── workspace/                  # Module 1 — multi-tenancy & auth
│   │   ├── models.py               # Workspace, ApiKey
│   │   ├── schemas.py
│   │   ├── service.py              # WorkspaceService
│   │   ├── dependencies.py        # FastAPI dependency: require_workspace
│   │   └── router.py
│   │
│   ├── journey/                    # Module 2 — cascading node/edge graph
│   │   ├── models.py               # Node, Edge
│   │   ├── schemas.py
│   │   ├── service.py              # JourneyService
│   │   ├── queries.py             # Recursive CTEs, DFS cycle detection
│   │   ├── tree.py                # Tree manipulation utilities
│   │   └── router.py
│   │
│   ├── ingestion/                  # Module 3 — data intake & normalization
│   │   ├── models.py               # DataSource, RawEvent, NormalizedEvent
│   │   ├── schemas.py
│   │   ├── service.py              # IngestionService
│   │   ├── normalizer.py          # JSONPath rule-based normalization
│   │   ├── classifier.py          # Pluggable NLP classifier (keyword impl included)
│   │   └── sources/               # Source adapters (webhook, file upload)
│   │
│   ├── mapping/                    # Module 4 — event-to-node signal mapping
│   │   ├── models.py               # MappingRule, MappedSignal, AutoMappingSuggestion
│   │   ├── schemas.py
│   │   ├── service.py              # MappingService
│   │   ├── engine.py              # Declarative rule evaluation engine
│   │   ├── auto_mapper.py         # Auto-mapping via input_schema matching
│   │   └── router.py
│   │
│   ├── goals/                      # Module 5 — product goals & KPIs
│   │   ├── models.py               # Goal, GoalSnapshot
│   │   ├── schemas.py
│   │   ├── service.py              # GoalService
│   │   ├── metrics.py             # Metric computation per GoalType
│   │   ├── scheduler.py           # Periodic snapshot computation hook
│   │   └── router.py
│   │
│   └── sonar/                      # Module 6 — scoring & focus map
│       ├── models.py               # NodeScore, SonarReport, FocusRecommendation
│       ├── schemas.py
│       ├── service.py              # SonarService
│       ├── scoring.py             # Health / Opportunity / Urgency / Composite algorithms
│       ├── cascading.py           # Score roll-up from children to parents
│       ├── anomaly.py             # Score change anomaly detection
│       └── router.py
│
├── tests/
│   ├── conftest.py                 # Shared fixtures
│   ├── test_mapping/test_engine.py # Rule evaluation unit tests
│   ├── test_ingestion/test_normalizer.py
│   └── test_sonar/test_scoring.py
│
├── alembic/                        # Database migrations
│   └── env.py
├── alembic.ini
├── docker-compose.yml              # PostgreSQL + app
├── Dockerfile
├── init_schemas.sql                # Creates 6 DB schemas on first startup
├── pyproject.toml
└── ARCHITECTURE.md
```

---

## Getting Started

### Requirements

- Python 3.12+
- Docker & Docker Compose (for PostgreSQL)

### 1. Clone & install

```bash
git clone https://github.com/BigSlikTobi/Journey_Sonar.git
cd Journey_Sonar

python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

### 2. Configure environment

Copy `.env` and adjust if needed:

```bash
cp .env .env.local
```

Default values work out of the box with Docker Compose:

```
CJM_DATABASE_URL=postgresql+asyncpg://journey:journey_dev@localhost:5432/journey_mapper
CJM_DEBUG=true
```

### 3. Start the database

```bash
docker-compose up -d db
```

### 4. Run migrations

```bash
alembic upgrade head
```

> **Note**: Alembic uses `psycopg2` for migrations (sync driver). Install it separately if needed: `pip install psycopg2-binary`

### 5. Start the API server

```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### 6. Run tests

```bash
pytest
```

---

## API Overview

All endpoints are prefixed with `/api/v1`. Authentication via `X-API-Key` header (except workspace creation).

### Workspace
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/workspaces` | Create a workspace |
| `GET` | `/workspaces/{id}` | Get workspace |
| `POST` | `/workspaces/{id}/api-keys` | Generate API key |

### Journey Engine
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/journey/nodes` | Create a node |
| `GET` | `/journey/nodes/{id}` | Get node |
| `GET` | `/journey/nodes/{id}/sub-journey` | Get child nodes |
| `GET` | `/journey/nodes/{id}/ancestors` | Get ancestor chain |
| `POST` | `/journey/edges` | Create an edge (with cycle detection) |
| `GET` | `/journey/nodes/match-inputs` | Match a data payload to nodes |

### Ingestion
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ingestion/sources` | Register a data source |
| `POST` | `/ingestion/sources/{id}/events` | Ingest a single event |
| `POST` | `/ingestion/sources/{id}/events/batch` | Ingest a batch |

### Mapping
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/mapping/rules` | Create a mapping rule |
| `GET` | `/mapping/rules` | List rules (filter by node) |
| `GET` | `/mapping/signals/by-node/{id}` | Signals for a journey node |

### Goals
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/goals` | Create a goal |
| `GET` | `/goals` | List goals |
| `GET` | `/goals/summary` | ON_TRACK / AT_RISK / OFF_TRACK counts |
| `POST` | `/goals/{id}/compute` | Force recompute snapshot |
| `GET` | `/goals/{id}/history` | Snapshot history |

### Sonar
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sonar/focus-map` | Ranked focus recommendations |
| `GET` | `/sonar/scores/{node_id}` | All scores for a node |
| `POST` | `/sonar/compute` | Trigger full workspace recomputation |

---

## Sonar Scoring

Each node receives four scores (0–100):

| Score | Meaning | Formula |
|-------|---------|---------|
| **Health** | How well is this node performing? | `(positive - negative) / total * 50 + 50` |
| **Opportunity** | How much improvement potential? | Weighted sum of goal gaps × priority |
| **Urgency** | How time-sensitive is action? | Max of: off-track goals, negative acceleration, cascading impact |
| **Composite** | Final ranking score | `0.35*(100-health) + 0.40*opportunity + 0.25*urgency` |

Scores **cascade upward**: a parent node's score is the volume-weighted average of its children's scores. So friction deep in "Onboarding > Connect Database" automatically surfaces to "Onboarding".

Weights are configurable per workspace in `Workspace.settings`.

---

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Database | Single PostgreSQL, 6 schemas | Operational simplicity, future extractability |
| Communication | In-process service calls + async event bus | Avoids microservice overhead; event bus is swappable for Redis Streams |
| Unstructured data | 3-stage pipeline: raw → normalize → classify | Classifier is pluggable — start with keywords, upgrade to LLM |
| Mapping rules | Declarative JSON conditions | No code changes to add rules; UI-editable |
| Goal metrics | Declarative metric definitions | Supports CONVERSION_RATE, THROUGHPUT, TIME_TO_COMPLETE, DROP_OFF_RATE |
| Cycle detection | DFS before every edge/parent assignment | Prevents infinite loops in the journey graph |

---

## Extending the System

### Add a new data source adapter
Implement in `app/ingestion/sources/`. Normalize the payload into the canonical `EventIngest` format and call `IngestionService.ingest_event()`.

### Upgrade the NLP classifier
Implement the `TextClassifier` Protocol from `app/ingestion/classifier.py` and inject it into `IngestionService`. The rest of the pipeline requires no changes.

### Add a new goal metric type
Add the type to `GoalType` in `app/common/types.py`, then add the computation function to `app/goals/metrics.py`.

### Scale to microservices
Each module owns a single PostgreSQL schema. Splitting a module to its own service means:
1. Moving its schema to its own database
2. Replacing in-process service calls with HTTP or gRPC calls
3. Replacing the in-process event bus subscriptions with a message broker

---

## Roadmap (next steps per module)

- **Ingestion**: LLM-based classifier, Zapier/Zendesk/Mixpanel connector library
- **Mapping**: Rule testing dry-run endpoint, auto-suggestion acceptance workflow
- **Goals**: Periodic snapshot scheduler (APScheduler/Celery Beat), alert notifications
- **Sonar**: Anomaly alert webhooks, score trend charts, configurable per-workspace weights
- **Journey**: Canvas export/import, journey versioning
