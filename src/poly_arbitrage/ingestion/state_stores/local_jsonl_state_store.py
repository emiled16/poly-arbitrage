from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.manifest import IngestionBatchManifest
from poly_arbitrage.ingestion.utils.clock import utc_now
from poly_arbitrage.ingestion.utils.serialization import stable_json_dumps


@dataclass(frozen=True, slots=True)
class RecordedFailure:
    job_id: str
    source: str
    dataset: str
    error_message: str
    recorded_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class LocalJsonlStateStore:
    root_directory: Path

    def record_success(self, job: IngestionJob, manifest: IngestionBatchManifest) -> None:
        self._append_event(
            event_type="success",
            event={
                "job": job,
                "manifest": manifest,
                "recorded_at": utc_now(),
            },
        )

    def record_failure(self, job: IngestionJob, error_message: str) -> None:
        self._append_event(
            event_type="failure",
            event=RecordedFailure(
                job_id=job.job_id,
                source=job.source,
                dataset=job.dataset,
                error_message=error_message,
            ),
        )

    def _append_event(self, *, event_type: str, event: object) -> None:
        path = self._event_log_path(event_type=event_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(stable_json_dumps(event))
            handle.write("\n")

    def _event_log_path(self, *, event_type: str) -> Path:
        now = utc_now().astimezone(UTC)
        return (
            self.root_directory
            / event_type
            / f"date={now:%Y-%m-%d}"
            / f"hour={now:%H}"
            / f"{event_type}.jsonl"
        )

