"""Shared exception hierarchy for consistent error handling."""

from __future__ import annotations

from uuid import UUID


class AppError(Exception):
    status_code: int = 500

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404

    def __init__(self, entity: str, entity_id: UUID | str) -> None:
        super().__init__(f"{entity} {entity_id} not found")


class ConflictError(AppError):
    status_code = 409


class ValidationError(AppError):
    status_code = 422


class AuthError(AppError):
    status_code = 401

    def __init__(self, detail: str = "Invalid or missing API key") -> None:
        super().__init__(detail)


class CycleDetectedError(ConflictError):
    def __init__(self, source_id: UUID, target_id: UUID) -> None:
        super().__init__(
            f"Edge from {source_id} to {target_id} would create a cycle"
        )
