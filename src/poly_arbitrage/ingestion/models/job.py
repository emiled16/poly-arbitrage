from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from poly_arbitrage.ingestion.models.job_status import IngestionJobStatus
from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class IngestionJob:
    job_id: str
    source: str
    dataset: str
    params: dict[str, Any]
    cursor: str | None = None
    checkpoint_key: str | None = None
    trigger: str = "manual"
    requested_at: datetime = field(default_factory=utc_now)
    available_at: datetime = field(default_factory=utc_now)
    status: IngestionJobStatus = IngestionJobStatus.PENDING
    attempts: int = 0
    worker_id: str | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_error: str | None = None
    idempotency_key: str | None = None
