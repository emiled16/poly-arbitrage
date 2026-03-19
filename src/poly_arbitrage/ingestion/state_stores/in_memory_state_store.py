from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.manifest import IngestionBatchManifest
from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class RecordedFailure:
    job_id: str
    source: str
    dataset: str
    error_message: str
    recorded_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class InMemoryStateStore:
    successes: list[IngestionBatchManifest] = field(default_factory=list)
    failures: list[RecordedFailure] = field(default_factory=list)

    def record_success(self, job: IngestionJob, manifest: IngestionBatchManifest) -> None:
        self.successes.append(manifest)

    def record_failure(self, job: IngestionJob, error_message: str) -> None:
        self.failures.append(
            RecordedFailure(
                job_id=job.job_id,
                source=job.source,
                dataset=job.dataset,
                error_message=error_message,
            )
        )
