from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class IngestionArtifact:
    batch_id: str
    job_id: str
    source: str
    dataset: str
    object_uri: str
    record_count: int
    next_cursor: str | None
    has_more: bool = False
    source_watermark: str | None = None
    stored_at: datetime = field(default_factory=utc_now)
