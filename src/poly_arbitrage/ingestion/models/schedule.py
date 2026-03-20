from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class IngestionSchedule:
    schedule_id: str
    name: str
    source: str
    dataset: str
    cadence_seconds: int
    params: dict[str, Any] = field(default_factory=dict)
    bootstrap_cursor: str | None = None
    trigger: str = "schedule"
    is_active: bool = True
    next_run_at: datetime = field(default_factory=utc_now)
    last_enqueued_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ClaimedIngestionSchedule:
    schedule: IngestionSchedule
    due_at: datetime
