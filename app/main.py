"""FastAPI application factory — registers all module routers."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.middleware.error_handling import register_error_handlers


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check and OPTIONS preflight
        if request.method == "OPTIONS" or request.url.path == "/health":
            return await call_next(request)
        if settings.api_key:
            key = request.headers.get("X-API-Key", "")
            if key != settings.api_key:
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)


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
    app.add_middleware(ApiKeyMiddleware)

    register_error_handlers(app)

    # --- Register module routers ---
    from app.workspace.router import router as workspace_router
    from app.journey.router import router as journey_router
    from app.ingestion.router import router as ingestion_router
    from app.mapping.router import router as mapping_router
    from app.goals.router import router as goals_router
    from app.sonar.router import router as sonar_router

    prefix = settings.api_prefix
    app.include_router(workspace_router, prefix=f"{prefix}/workspaces", tags=["workspace"])
    app.include_router(journey_router, prefix=f"{prefix}/journey", tags=["journey"])
    app.include_router(ingestion_router, prefix=f"{prefix}/ingestion", tags=["ingestion"])
    app.include_router(mapping_router, prefix=f"{prefix}/mapping", tags=["mapping"])
    app.include_router(goals_router, prefix=f"{prefix}/goals", tags=["goals"])
    app.include_router(sonar_router, prefix=f"{prefix}/sonar", tags=["sonar"])

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
