"""Middleware that resolves the workspace from the API key on each request."""

from __future__ import annotations

from contextvars import ContextVar
from uuid import UUID

from fastapi import Depends, Header

from app.common.exceptions import AuthError
from app.common.schemas import WorkspaceContext

_workspace_ctx: ContextVar[WorkspaceContext | None] = ContextVar(
    "workspace_ctx", default=None
)


def get_workspace_context() -> WorkspaceContext:
    ctx = _workspace_ctx.get()
    if ctx is None:
        raise AuthError("No workspace context — missing or invalid API key")
    return ctx


def set_workspace_context(ctx: WorkspaceContext) -> None:
    _workspace_ctx.set(ctx)


async def require_workspace(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> WorkspaceContext:
    """FastAPI dependency that authenticates via API key and returns workspace context.

    Actual key validation delegated to WorkspaceService (injected at app startup).
    This stub returns a placeholder — wire up WorkspaceService.validate_api_key() in
    the workspace module's dependencies.py.
    """
    if not x_api_key:
        raise AuthError()
    # Placeholder: replaced by real validation in workspace/dependencies.py
    raise AuthError("API key validation not yet wired")
