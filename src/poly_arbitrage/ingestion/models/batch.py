from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from poly_arbitrage.ingestion.models.raw_record import RawIngestionRecord
from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class IngestionBatch:
    source: str
    dataset: str
    job_id: str
    records: list[RawIngestionRecord]
    next_cursor: str | None = None
    batch_id: str = field(default_factory=lambda: uuid4().hex)
    emitted_at: datetime = field(default_factory=utc_now)
