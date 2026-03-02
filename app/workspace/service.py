"""Workspace module service — business logic for workspaces and API keys."""

from __future__ import annotations

import secrets
import uuid
from typing import Protocol

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AuthError, ConflictError, NotFoundError
from app.workspace.models import ApiKey, Workspace
from app.workspace.schemas import ApiKeyCreate, WorkspaceCreate, WorkspaceUpdate


class WorkspaceServiceProtocol(Protocol):
    async def get_workspace(self, session: AsyncSession, workspace_id: uuid.UUID) -> Workspace: ...
    async def validate_api_key(
        self, session: AsyncSession, raw_key: str
    ) -> tuple[Workspace, list[str]]: ...


class WorkspaceService:
    # --- Workspace CRUD ---

    async def create_workspace(
        self, session: AsyncSession, data: WorkspaceCreate
    ) -> Workspace:
        existing = await session.execute(
            select(Workspace).where(Workspace.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Workspace slug '{data.slug}' already exists")

        ws = Workspace(name=data.name, slug=data.slug, settings=data.settings)
        session.add(ws)
        await session.flush()
        return ws

    async def get_workspace(
        self, session: AsyncSession, workspace_id: uuid.UUID
    ) -> Workspace:
        ws = await session.get(Workspace, workspace_id)
        if not ws or not ws.is_active:
            raise NotFoundError("Workspace", workspace_id)
        return ws

    async def update_workspace(
        self, session: AsyncSession, workspace_id: uuid.UUID, data: WorkspaceUpdate
    ) -> Workspace:
        ws = await self.get_workspace(session, workspace_id)
        if data.name is not None:
            ws.name = data.name
        if data.settings is not None:
            ws.settings = data.settings
        await session.flush()
        return ws

    # --- API Key Management ---

    async def create_api_key(
        self, session: AsyncSession, workspace_id: uuid.UUID, data: ApiKeyCreate
    ) -> tuple[ApiKey, str]:
        """Returns (ApiKey model, raw_key). Raw key is only available here."""
        await self.get_workspace(session, workspace_id)  # Validate workspace exists

        raw_key = f"cjm_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:8]
        key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()

        api_key = ApiKey(
            workspace_id=workspace_id,
            key_hash=key_hash,
            prefix=prefix,
            label=data.label,
            scopes=data.scopes,
        )
        session.add(api_key)
        await session.flush()
        return api_key, raw_key

    async def validate_api_key(
        self, session: AsyncSession, raw_key: str
    ) -> tuple[Workspace, list[str]]:
        """Validate an API key and return (workspace, scopes). Raises AuthError on failure."""
        prefix = raw_key[:8]
        result = await session.execute(
            select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.is_active.is_(True))
        )
        api_key = result.scalar_one_or_none()

        if not api_key or not bcrypt.checkpw(raw_key.encode(), api_key.key_hash.encode()):
            raise AuthError()

        ws = await self.get_workspace(session, api_key.workspace_id)
        return ws, api_key.scopes
