"""Pydantic models for validating imported journey JSON files."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EmailEntry(BaseModel):
    name: str
    subject: str


class TouchpointImport(BaseModel):
    touchpoint: str = Field(..., min_length=1)
    businessRule: str = ""
    feature: str = ""
    dataPoints: list[str] = Field(default_factory=list)
    edgeCases: list[str] = Field(default_factory=list)
    emails: list[EmailEntry] = Field(default_factory=list)


class StageImport(BaseModel):
    title: str = Field(..., min_length=1)
    items: list[TouchpointImport] = Field(default_factory=list)


class JourneyImport(BaseModel):
    journeyName: str = Field(..., min_length=1)
    version: str = "1.0"
    stages: list[StageImport] = Field(..., min_length=1)
