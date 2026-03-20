from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from poly_arbitrage.ingestion.models.artifact import IngestionArtifact
from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.job_status import IngestionJobStatus
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.models.schedule import ClaimedIngestionSchedule, IngestionSchedule


class ObjectStore(Protocol):
    def ensure_container(self, container_name: str) -> None:
        """Ensure the named container exists."""

    def put_bytes(
        self,
        *,
        container_name: str,
        object_key: str,
        payload: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Persist one object and return a stable object URI."""

    def get_bytes(self, *, container_name: str, object_key: str) -> bytes:
        """Read one object payload."""


class SourceHandler(Protocol):
    source_name: str
    dataset_name: str

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        """Fetch one raw batch for a source-specific ingestion job."""


class IngestionJobQueue(Protocol):
    def publish(self, job_id: str) -> None:
        """Publish one job id to the delivery queue."""

    def consume(self, handler: Callable[[str], None]) -> None:
        """Consume job ids and invoke the handler for each one."""


class JobRepository(Protocol):
    def create_job(
        self,
        request: IngestionRequest,
        *,
        available_at: datetime | None = None,
    ) -> IngestionJob:
        """Persist a new job and return its stored state."""

    def get_job(self, job_id: str) -> IngestionJob | None:
        """Load one job by id."""

    def get_job_by_idempotency_key(
        self,
        *,
        source: str,
        dataset: str,
        idempotency_key: str,
    ) -> IngestionJob | None:
        """Load one job by idempotency key for duplicate-request handling."""

    def list_jobs(
        self,
        *,
        status: IngestionJobStatus | None = None,
        source: str | None = None,
        dataset: str | None = None,
        limit: int = 100,
    ) -> list[IngestionJob]:
        """List jobs using simple operational filters."""

    def list_retry_ready(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[IngestionJob]:
        """List retry-pending jobs that are due to be re-enqueued."""

    def mark_queued(self, job_id: str, *, queued_at: datetime) -> IngestionJob:
        """Persist that a job id was handed to the queue."""

    def mark_running(self, job_id: str, *, worker_id: str) -> IngestionJob:
        """Transition a job into the running state."""

    def mark_succeeded(self, job_id: str, artifact: IngestionArtifact) -> IngestionJob:
        """Persist successful completion details for a job."""

    def mark_retry_pending(
        self,
        job_id: str,
        *,
        error_message: str,
        available_at: datetime,
    ) -> IngestionJob:
        """Persist a retryable failure and the next available retry time."""

    def mark_failed(self, job_id: str, *, error_message: str) -> IngestionJob:
        """Persist failure details for a job."""

    def mark_dead_lettered(self, job_id: str, *, error_message: str) -> IngestionJob:
        """Persist that a job exhausted retries and entered the dead-letter state."""


class CursorRepository(Protocol):
    def advance_cursor(
        self,
        *,
        source: str,
        dataset: str,
        checkpoint_key: str,
        cursor: str,
        expected_cursor: str | None,
    ) -> bool:
        """Persist the latest known cursor if the current value still matches."""

    def get_cursor(
        self,
        *,
        source: str,
        dataset: str,
        checkpoint_key: str,
    ) -> str | None:
        """Load the latest known cursor for a source dataset and checkpoint owner."""


class ScheduleRepository(Protocol):
    def create_schedule(self, schedule: IngestionSchedule) -> IngestionSchedule:
        """Persist one schedule definition."""

    def list_schedules(
        self,
        *,
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[IngestionSchedule]:
        """List schedule definitions for operational inspection."""

    def claim_due_schedules(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[ClaimedIngestionSchedule]:
        """Atomically claim due schedules and advance their next run times."""
