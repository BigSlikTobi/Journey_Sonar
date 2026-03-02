"""Data Ingestion Pipeline service — raw event capture, normalization, classification."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.types import ProcessingStatus
from app.events import event_bus
from app.ingestion.classifier import KeywordClassifier, TextClassifier
from app.ingestion.models import DataSource, NormalizedEvent, RawEvent
from app.ingestion.normalizer import build_normalized_fields
from app.ingestion.schemas import DataSourceCreate, DataSourceUpdate, EventIngest


class IngestionService:
    def __init__(self, classifier: TextClassifier | None = None) -> None:
        self._classifier = classifier or KeywordClassifier()

    # --- DataSource CRUD ---

    async def create_source(
        self, session: AsyncSession, workspace_id: uuid.UUID, data: DataSourceCreate
    ) -> DataSource:
        source = DataSource(
            workspace_id=workspace_id,
            name=data.name,
            source_type=data.source_type,
            config=data.config,
            normalization_rules=data.normalization_rules,
        )
        session.add(source)
        await session.flush()
        return source

    async def get_source(
        self, session: AsyncSession, workspace_id: uuid.UUID, source_id: uuid.UUID
    ) -> DataSource:
        source = await session.get(DataSource, source_id)
        if not source or source.workspace_id != workspace_id:
            raise NotFoundError("DataSource", source_id)
        return source

    async def list_sources(
        self, session: AsyncSession, workspace_id: uuid.UUID
    ) -> list[DataSource]:
        result = await session.execute(
            select(DataSource).where(
                DataSource.workspace_id == workspace_id, DataSource.is_active.is_(True)
            )
        )
        return list(result.scalars().all())

    async def update_source(
        self, session: AsyncSession, workspace_id: uuid.UUID,
        source_id: uuid.UUID, data: DataSourceUpdate
    ) -> DataSource:
        source = await self.get_source(session, workspace_id, source_id)
        if data.name is not None:
            source.name = data.name
        if data.config is not None:
            source.config = data.config
        if data.normalization_rules is not None:
            source.normalization_rules = data.normalization_rules
        if data.is_active is not None:
            source.is_active = data.is_active
        await session.flush()
        return source

    # --- Event Ingestion ---

    async def ingest_event(
        self, session: AsyncSession, workspace_id: uuid.UUID,
        source_id: uuid.UUID, data: EventIngest
    ) -> NormalizedEvent:
        """Ingest a single raw event: store raw, normalize, classify, emit."""
        source = await self.get_source(session, workspace_id, source_id)

        # Stage 1: Raw capture
        raw = RawEvent(
            workspace_id=workspace_id,
            source_id=source_id,
            external_id=data.external_id,
            raw_payload=data.payload,
        )
        session.add(raw)
        await session.flush()

        # Stage 2: Normalize
        fields = build_normalized_fields(data.payload, source.normalization_rules)

        # Stage 3: Classify unstructured text (if present)
        classification = None
        text_content = _extract_text_content(data.payload)
        if text_content:
            classification = await self._classifier.classify(text_content)
            classification = classification.model_dump()

        normalized = NormalizedEvent(
            workspace_id=workspace_id,
            raw_event_id=raw.id,
            source_id=source_id,
            event_type=fields["event_type"],
            actor_id=fields.get("actor_id"),
            properties=fields["properties"],
            occurred_at=data.occurred_at or fields.get("occurred_at", datetime.now(timezone.utc)),
            processing_status=ProcessingStatus.PROCESSED,
            classification=classification,
        )
        session.add(normalized)
        await session.flush()

        # Emit event for Mapping Engine
        await event_bus.publish("ingestion.event.normalized", {
            "workspace_id": str(workspace_id),
            "normalized_event_id": str(normalized.id),
            "event_type": normalized.event_type,
            "actor_id": normalized.actor_id,
            "properties": normalized.properties,
            "classification": normalized.classification,
            "occurred_at": normalized.occurred_at.isoformat(),
        })

        return normalized

    async def ingest_batch(
        self, session: AsyncSession, workspace_id: uuid.UUID,
        source_id: uuid.UUID, events: list[EventIngest]
    ) -> list[NormalizedEvent]:
        results = []
        for event_data in events:
            normalized = await self.ingest_event(session, workspace_id, source_id, event_data)
            results.append(normalized)
        return results


def _extract_text_content(payload: dict) -> str | None:
    """Heuristic: look for common text fields in the payload for NLP classification."""
    for key in ("body", "description", "text", "message", "content", "comment"):
        if key in payload and isinstance(payload[key], str) and len(payload[key]) > 20:
            return payload[key]
    return None
