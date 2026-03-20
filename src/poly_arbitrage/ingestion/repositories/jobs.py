from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import uuid4

from poly_arbitrage.ingestion.database.records.job_records import IngestionJobRecord
from poly_arbitrage.ingestion.database.registry import RepositoryRegistry
from poly_arbitrage.ingestion.models.artifact import IngestionArtifact
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.job_status import IngestionJobStatus
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(slots=True)
class JobRepository:
    registry: RepositoryRegistry

    def create_job(
        self,
        request: IngestionRequest,
        *,
        available_at: datetime | None = None,
    ) -> IngestionJob:
        if request.idempotency_key is not None:
            existing = self.registry.job_records.get_by_idempotency_key(
                source=request.source,
                dataset=request.dataset,
                idempotency_key=request.idempotency_key,
            )
            if existing is not None:
                return self._to_job(existing)
        record = IngestionJobRecord(
            job_id=uuid4().hex,
            source=request.source,
            dataset=request.dataset,
            params=dict(request.params),
            cursor=request.cursor,
            checkpoint_key=request.checkpoint_key,
            trigger=request.trigger,
            requested_at=request.requested_at,
            available_at=available_at or request.requested_at,
            status=IngestionJobStatus.PENDING.value,
            attempts=0,
            worker_id=None,
            queued_at=None,
            started_at=None,
            completed_at=None,
            last_error=None,
            idempotency_key=request.idempotency_key,
            batch_id=None,
            object_uri=None,
            record_count=None,
            next_cursor=None,
            has_more=False,
            source_watermark=None,
        )
        return self._to_job(self.registry.save(record))

    def get_job(self, job_id: str) -> IngestionJob | None:
        record = self.registry.job_records.get(job_id)
        if record is None:
            return None
        return self._to_job(record)

    def get_job_by_idempotency_key(
        self,
        *,
        source: str,
        dataset: str,
        idempotency_key: str,
    ) -> IngestionJob | None:
        record = self.registry.job_records.get_by_idempotency_key(
            source=source,
            dataset=dataset,
            idempotency_key=idempotency_key,
        )
        if record is None:
            return None
        return self._to_job(record)

    def list_jobs(
        self,
        *,
        status: IngestionJobStatus | None = None,
        source: str | None = None,
        dataset: str | None = None,
        limit: int = 100,
    ) -> list[IngestionJob]:
        return [
            self._to_job(record)
            for record in self.registry.job_records.list(
                status=None if status is None else status.value,
                source=source,
                dataset=dataset,
                limit=limit,
            )
        ]

    def list_retry_ready(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[IngestionJob]:
        return [
            self._to_job(record)
            for record in self.registry.job_records.list_retry_ready(now=now, limit=limit)
        ]

    def mark_queued(self, job_id: str, *, queued_at: datetime) -> IngestionJob:
        current = self.registry.job_records.get(job_id)
        if current is None:
            raise KeyError(f"unknown job_id={job_id!r}")
        updated = replace(current, queued_at=queued_at)
        return self._to_job(self.registry.save(updated))

    def mark_running(self, job_id: str, *, worker_id: str) -> IngestionJob:
        current = self.registry.job_records.get(job_id)
        if current is None:
            raise KeyError(f"unknown job_id={job_id!r}")
        if current.status not in {
            IngestionJobStatus.PENDING.value,
            IngestionJobStatus.RETRY_PENDING.value,
        }:
            raise RuntimeError(
                f"job {job_id!r} cannot transition to running from status={current.status!r}"
            )
        if current.available_at > utc_now():
            raise RuntimeError(f"job {job_id!r} is not available to run yet")
        updated = replace(
            current,
            status=IngestionJobStatus.RUNNING.value,
            attempts=current.attempts + 1,
            worker_id=worker_id,
            started_at=utc_now(),
            completed_at=None,
            last_error=None,
        )
        return self._to_job(self.registry.save(updated))

    def mark_succeeded(self, job_id: str, artifact: IngestionArtifact) -> IngestionJob:
        current = self.registry.job_records.get(job_id)
        if current is None:
            raise KeyError(f"unknown job_id={job_id!r}")
        updated = replace(
            current,
            status=IngestionJobStatus.SUCCEEDED.value,
            completed_at=artifact.stored_at,
            last_error=None,
            batch_id=artifact.batch_id,
            object_uri=artifact.object_uri,
            record_count=artifact.record_count,
            next_cursor=artifact.next_cursor,
            has_more=artifact.has_more,
            source_watermark=artifact.source_watermark,
        )
        return self._to_job(self.registry.save(updated))

    def mark_retry_pending(
        self,
        job_id: str,
        *,
        error_message: str,
        available_at: datetime,
    ) -> IngestionJob:
        current = self.registry.job_records.get(job_id)
        if current is None:
            raise KeyError(f"unknown job_id={job_id!r}")
        updated = replace(
            current,
            status=IngestionJobStatus.RETRY_PENDING.value,
            available_at=available_at,
            queued_at=None,
            completed_at=None,
            last_error=error_message,
        )
        return self._to_job(self.registry.save(updated))

    def mark_failed(self, job_id: str, *, error_message: str) -> IngestionJob:
        current = self.registry.job_records.get(job_id)
        if current is None:
            raise KeyError(f"unknown job_id={job_id!r}")
        updated = replace(
            current,
            status=IngestionJobStatus.FAILED.value,
            completed_at=utc_now(),
            last_error=error_message,
        )
        return self._to_job(self.registry.save(updated))

    def mark_dead_lettered(self, job_id: str, *, error_message: str) -> IngestionJob:
        current = self.registry.job_records.get(job_id)
        if current is None:
            raise KeyError(f"unknown job_id={job_id!r}")
        updated = replace(
            current,
            status=IngestionJobStatus.DEAD_LETTERED.value,
            completed_at=utc_now(),
            last_error=error_message,
        )
        return self._to_job(self.registry.save(updated))

    def _to_job(self, record: IngestionJobRecord) -> IngestionJob:
        return IngestionJob(
            job_id=record.job_id,
            source=record.source,
            dataset=record.dataset,
            params=dict(record.params),
            cursor=record.cursor,
            checkpoint_key=record.checkpoint_key,
            trigger=record.trigger,
            requested_at=record.requested_at,
            available_at=record.available_at,
            status=IngestionJobStatus(record.status),
            attempts=record.attempts,
            worker_id=record.worker_id,
            queued_at=record.queued_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            last_error=record.last_error,
            idempotency_key=record.idempotency_key,
        )
