"""FastAPI dependencies for workspace-scoped request context."""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AuthError
from app.common.schemas import WorkspaceContext
from app.database import get_session
from app.workspace.service import WorkspaceService

_workspace_service = WorkspaceService()


async def require_workspace(
    session: AsyncSession = Depends(get_session),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> WorkspaceContext:
    """Authenticate via API key and return workspace context for this request."""
    if not x_api_key:
        raise AuthError()

    ws, scopes = await _workspace_service.validate_api_key(session, x_api_key)
    return WorkspaceContext(workspace_id=ws.id, scopes=scopes)
