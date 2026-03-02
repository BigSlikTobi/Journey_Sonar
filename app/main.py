"""FastAPI application factory — registers all module routers."""

from fastapi import FastAPI

from app.config import settings
from app.middleware.error_handling import register_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="Customer Journey Mapper",
        version="0.1.0",
        debug=settings.debug,
    )

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

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
