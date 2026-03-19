from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class IngestionBatchManifest:
    batch_id: str
    job_id: str
    source: str
    dataset: str
    object_uri: str
    record_count: int
    next_cursor: str | None
    stored_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class ProcessedIngestionJob:
    job: IngestionJob
    manifest: IngestionBatchManifest
