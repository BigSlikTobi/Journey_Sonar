"""FastAPI application factory — registers all module routers."""

import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.middleware.error_handling import register_error_handlers


async def verify_api_key(request: Request) -> None:
    if not settings.api_key:
        return
    key = request.headers.get("X-API-Key", "")
    if key != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Customer Journey Mapper",
        version="0.1.0",
        debug=settings.debug,
    )

    origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    # --- Register module routers (all protected by API key) ---
    from app.workspace.router import router as workspace_router
    from app.journey.router import router as journey_router
    from app.ingestion.router import router as ingestion_router
    from app.mapping.router import router as mapping_router
    from app.goals.router import router as goals_router
    from app.sonar.router import router as sonar_router

    api_deps = [Depends(verify_api_key)]
    prefix = settings.api_prefix
    app.include_router(workspace_router, prefix=f"{prefix}/workspaces", tags=["workspace"], dependencies=api_deps)
    app.include_router(journey_router, prefix=f"{prefix}/journey", tags=["journey"], dependencies=api_deps)
    app.include_router(ingestion_router, prefix=f"{prefix}/ingestion", tags=["ingestion"], dependencies=api_deps)
    app.include_router(mapping_router, prefix=f"{prefix}/mapping", tags=["mapping"], dependencies=api_deps)
    app.include_router(goals_router, prefix=f"{prefix}/goals", tags=["goals"], dependencies=api_deps)
    app.include_router(sonar_router, prefix=f"{prefix}/sonar", tags=["sonar"], dependencies=api_deps)

    # --- Wire up event subscriptions ---
    from app.events import event_bus  # noqa: F811
    from app.mapping.service import MappingService
    from app.sonar.service import SonarService

    mapping_svc = MappingService()
    sonar_svc = SonarService()

    event_bus.subscribe("ingestion.event.normalized", mapping_svc.handle_normalized_event)
    event_bus.subscribe("mapping.signal.created", sonar_svc.handle_new_signal)

    @app.on_event("startup")
    async def startup() -> None:
        from app.database import create_tables
        await create_tables()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Serve built frontend — only present after `npm run build`
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
    if os.path.isdir(dist_dir):
        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

    return app


app = create_app()
