"""Database models for run tracking."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlmodel import Column, Field, SQLModel
from sqlalchemy import Text
import json


class Run(SQLModel, table=True):
    """A workflow execution."""

    __tablename__ = "runs"

    id: str = Field(primary_key=True)
    workflow: str
    status: str = "pending"  # pending | claimed | running | completed | failed
    inputs: str = "{}"  # JSON string
    result: str | None = None  # JSON string
    error: str | None = None
    worker_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def get_inputs(self) -> dict[str, Any]:
        return json.loads(self.inputs) if self.inputs else {}

    def get_result(self) -> dict[str, Any] | None:
        return json.loads(self.result) if self.result else None


class RunEvent(SQLModel, table=True):
    """An event emitted during a run — written by worker, read by API."""

    __tablename__ = "run_events"

    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    event_type: str  # stage_start, agent_start, stream_chunk, etc.
    data: str = "{}"  # JSON payload
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
