"""Auto-mapping: fallback that uses Journey Engine input_schema matching.

When no explicit MappingRule matches an event, this module attempts to
match the event's properties against node input_schemas and creates
AutoMappingSuggestion records for human review.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.types import SuggestionStatus
from app.journey.service import JourneyService
from app.mapping.models import AutoMappingSuggestion

AUTO_MAP_CONFIDENCE_THRESHOLD = 0.7


async def suggest_mappings(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    normalized_event_id: uuid.UUID,
    event_properties: dict,
    journey_service: JourneyService,
) -> list[AutoMappingSuggestion]:
    """Try to auto-map an event to journey nodes using input_schema matching.

    Creates suggestion records for matches above the confidence threshold.
    """
    matches = await journey_service.match_node_by_input(
        session, workspace_id, event_properties
    )

    suggestions = []
    for match in matches:
        if match.confidence < AUTO_MAP_CONFIDENCE_THRESHOLD:
            continue

        suggestion = AutoMappingSuggestion(
            workspace_id=workspace_id,
            normalized_event_id=normalized_event_id,
            suggested_node_id=match.node_id,
            confidence=match.confidence,
            reasoning=f"Matched fields: {', '.join(match.matched_fields)}",
            status=SuggestionStatus.PENDING,
        )
        session.add(suggestion)
        suggestions.append(suggestion)

    if suggestions:
        await session.flush()

    return suggestions
