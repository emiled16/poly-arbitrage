from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from poly_arbitrage.ingestion.contracts import CursorRepository, IngestionJobQueue, JobRepository
from poly_arbitrage.ingestion.models.artifact import IngestionArtifact
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.job_status import IngestionJobStatus
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.raw_storage.raw_batch_storage import RawBatchStorage
from poly_arbitrage.ingestion.registry import SourceRegistry
from poly_arbitrage.ingestion.settings import RetrySettings
from poly_arbitrage.ingestion.submission import normalize_request
from poly_arbitrage.ingestion.utils.clock import utc_now

LOGGER = logging.getLogger(__name__)


class StaleCursorUpdateError(RuntimeError):
    pass


@dataclass(slots=True)
class IngestionService:
    """Service for submitting ingestion requests and managing ingestion jobs."""

    job_repository: JobRepository
    cursor_repository: CursorRepository
    source_registry: SourceRegistry
    raw_storage: RawBatchStorage
    retry_settings: RetrySettings
    job_queue: IngestionJobQueue | None = None

    def submit_request(
        self,
        request: IngestionRequest,
        *,
        available_at: datetime | None = None,
        publish: bool = True,
    ) -> IngestionJob:
        request = normalize_request(request)
        existing_job = None
        if request.idempotency_key is not None:
            existing_job = self.job_repository.get_job_by_idempotency_key(
                source=request.source,
                dataset=request.dataset,
                idempotency_key=request.idempotency_key,
            )
        job = self.job_repository.create_job(request, available_at=available_at)
        if publish and existing_job is None:
            self.publish_job(job.job_id)
        if existing_job is not None:
            LOGGER.info(
                "ingestion duplicate enqueue collapsed",
                extra={
                    "source": request.source,
                    "dataset": request.dataset,
                    "idempotency_key": request.idempotency_key,
                    "checkpoint_key": request.checkpoint_key,
                },
            )
        return job

    def publish_job(self, job_id: str) -> IngestionJob:
        if self.job_queue is None:
            raise RuntimeError("job queue is not configured")
        self.job_queue.publish(job_id)
        return self.job_repository.mark_queued(job_id, queued_at=utc_now())

    def redrive_job(self, job_id: str, *, publish: bool = True) -> IngestionJob:
        """Redrive a job by submitting a new request with the same idempotency key."""
        job = self.job_repository.get_job(job_id)
        if job is None:
            raise KeyError(f"unknown job_id={job_id!r}")
        return self.submit_request(
            IngestionRequest(
                source=job.source,
                dataset=job.dataset,
                params=dict(job.params),
                cursor=job.cursor,
                trigger="admin-redrive",
                idempotency_key=None,
            ),
            publish=publish,
        )

    def run_job(self, job_id: str, *, worker_id: str) -> IngestionArtifact:
        job = self.job_repository.get_job(job_id)
        if job is None:
            raise KeyError(f"unknown job_id={job_id!r}")

        if job.status == IngestionJobStatus.SUCCEEDED:
            raise RuntimeError(f"job {job_id!r} has already succeeded")

        running_job = self.job_repository.mark_running(job_id, worker_id=worker_id)
        handler = self.source_registry.get(running_job.source, running_job.dataset)

        try:
            batch = handler.fetch(running_job)
            artifact = self.raw_storage.store_batch(batch)
            self._advance_cursor(running_job, artifact)
            self.job_repository.mark_succeeded(job_id, artifact)
            self._log_success(running_job, artifact)
            return artifact
        except StaleCursorUpdateError as exc:
            self.job_repository.mark_failed(job_id, error_message=str(exc))
            raise
        except Exception as exc:
            LOGGER.exception("ingestion job failed", extra={"job_id": job_id})
            self._record_failure(running_job, error_message=str(exc))
            raise

    def _advance_cursor(self, job: IngestionJob, artifact: IngestionArtifact) -> None:
        if artifact.next_cursor is None or job.checkpoint_key is None:
            return
        advanced = self.cursor_repository.advance_cursor(
            source=artifact.source,
            dataset=artifact.dataset,
            checkpoint_key=job.checkpoint_key,
            cursor=artifact.next_cursor,
            expected_cursor=job.cursor,
        )
        if not advanced:
            raise StaleCursorUpdateError(
                "checkpoint cursor changed before this job completed "
                f"(source={artifact.source}, dataset={artifact.dataset}, "
                f"checkpoint_key={job.checkpoint_key})"
            )

    def _log_success(self, job: IngestionJob, artifact: IngestionArtifact) -> None:
        LOGGER.info(
            "ingestion job succeeded",
            extra={
                "job_id": job.job_id,
                "source": artifact.source,
                "dataset": artifact.dataset,
                "checkpoint_before": job.cursor,
                "checkpoint_after": artifact.next_cursor,
                "checkpoint_key": job.checkpoint_key,
                "query_mode": job.params.get("mode"),
                "has_more": artifact.has_more,
                "retries": max(job.attempts - 1, 0),
            },
        )

    def _record_failure(self, job: IngestionJob, *, error_message: str) -> None:
        if job.attempts >= self.retry_settings.max_attempts:
            self.job_repository.mark_dead_lettered(job.job_id, error_message=error_message)
            return

        retry_delay_seconds = self.retry_settings.delay_seconds_for_attempt(job.attempts)
        retry_at = utc_now() + timedelta(seconds=retry_delay_seconds)
        retry_job = self.job_repository.mark_retry_pending(
            job.job_id,
            error_message=error_message,
            available_at=retry_at,
        )
        if retry_job.available_at <= utc_now():
            self.publish_job(job.job_id)
