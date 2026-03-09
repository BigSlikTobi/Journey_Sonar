"""Provides a default workspace for unauthenticated access."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import WorkspaceContext
from app.database import get_session
from app.workspace.models import Workspace

_DEFAULT_SLUG = "default"


async def default_workspace(
    session: AsyncSession = Depends(get_session),
) -> WorkspaceContext:
    """Return (or create) the default workspace. No API key required."""
    result = await session.execute(
        select(Workspace).where(Workspace.slug == _DEFAULT_SLUG)
    )
    ws = result.scalar_one_or_none()

    if not ws:
        try:
            ws = Workspace(name="Default", slug=_DEFAULT_SLUG, settings={})
            session.add(ws)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            result = await session.execute(
                select(Workspace).where(Workspace.slug == _DEFAULT_SLUG)
            )
            ws = result.scalar_one()

    return WorkspaceContext(workspace_id=ws.id, scopes=[])
