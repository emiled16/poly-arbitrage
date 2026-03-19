from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class IngestionJob:
    job_id: str
    source: str
    dataset: str
    params: dict[str, Any]
    cursor: str | None = None
    enqueued_at: datetime = field(default_factory=utc_now)
