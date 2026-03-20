from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from poly_arbitrage.ingestion.models.artifact import IngestionArtifact
from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.job_status import IngestionJobStatus
from poly_arbitrage.ingestion.models.raw_record import build_raw_record
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.object_stores.local import LocalFilesystemObjectStore
from poly_arbitrage.ingestion.raw_storage.raw_batch_storage import RawBatchStorage
from poly_arbitrage.ingestion.registry import build_registry
from poly_arbitrage.ingestion.service import IngestionService, StaleCursorUpdateError
from poly_arbitrage.ingestion.settings import RetrySettings
from poly_arbitrage.ingestion.workers.consumer import IngestionWorkerConsumer


class FakeJobQueue:
    def __init__(self) -> None:
        self.published_job_ids: list[str] = []
        self.consumer = None

    def publish(self, job_id: str) -> None:
        self.published_job_ids.append(job_id)

    def consume(self, handler) -> None:
        self.consumer = handler


class FakeJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, IngestionJob] = {}

    def create_job(
        self,
        request: IngestionRequest,
        *,
        available_at=None,
    ) -> IngestionJob:
        if request.idempotency_key is not None:
            existing = self.get_job_by_idempotency_key(
                source=request.source,
                dataset=request.dataset,
                idempotency_key=request.idempotency_key,
            )
            if existing is not None:
                return existing
        job = IngestionJob(
            job_id=f"job-{len(self.jobs) + 1}",
            source=request.source,
            dataset=request.dataset,
            params=dict(request.params),
            cursor=request.cursor,
            checkpoint_key=request.checkpoint_key,
            trigger=request.trigger,
            requested_at=request.requested_at,
            available_at=available_at or request.requested_at,
            idempotency_key=request.idempotency_key,
        )
        self.jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> IngestionJob | None:
        return self.jobs.get(job_id)

    def get_job_by_idempotency_key(
        self,
        *,
        source: str,
        dataset: str,
        idempotency_key: str,
    ) -> IngestionJob | None:
        for job in self.jobs.values():
            if (
                job.source == source
                and job.dataset == dataset
                and job.idempotency_key == idempotency_key
            ):
                return job
        return None

    def list_jobs(
        self,
        *,
        status: IngestionJobStatus | None = None,
        source: str | None = None,
        dataset: str | None = None,
        limit: int = 100,
    ) -> list[IngestionJob]:
        jobs = list(self.jobs.values())
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        if source is not None:
            jobs = [job for job in jobs if job.source == source]
        if dataset is not None:
            jobs = [job for job in jobs if job.dataset == dataset]
        return jobs[:limit]

    def list_retry_ready(self, *, now, limit: int = 100) -> list[IngestionJob]:
        return [
            job
            for job in self.jobs.values()
            if job.status == IngestionJobStatus.RETRY_PENDING
            and job.available_at <= now
            and job.queued_at is None
        ][:limit]

    def mark_queued(self, job_id: str, *, queued_at) -> IngestionJob:
        job = self.jobs[job_id]
        updated = replace(job, queued_at=queued_at)
        self.jobs[job_id] = updated
        return updated

    def mark_running(self, job_id: str, *, worker_id: str) -> IngestionJob:
        job = self.jobs[job_id]
        updated = replace(
            job,
            status=IngestionJobStatus.RUNNING,
            attempts=job.attempts + 1,
            worker_id=worker_id,
        )
        self.jobs[job_id] = updated
        return updated

    def mark_succeeded(self, job_id: str, artifact: IngestionArtifact) -> IngestionJob:
        job = self.jobs[job_id]
        updated = replace(
            job,
            status=IngestionJobStatus.SUCCEEDED,
            completed_at=artifact.stored_at,
            last_error=None,
        )
        self.jobs[job_id] = updated
        return updated

    def mark_retry_pending(self, job_id: str, *, error_message: str, available_at) -> IngestionJob:
        job = self.jobs[job_id]
        updated = replace(
            job,
            status=IngestionJobStatus.RETRY_PENDING,
            available_at=available_at,
            queued_at=None,
            completed_at=None,
            last_error=error_message,
        )
        self.jobs[job_id] = updated
        return updated

    def mark_failed(self, job_id: str, *, error_message: str) -> IngestionJob:
        job = self.jobs[job_id]
        updated = replace(
            job,
            status=IngestionJobStatus.FAILED,
            last_error=error_message,
        )
        self.jobs[job_id] = updated
        return updated

    def mark_dead_lettered(self, job_id: str, *, error_message: str) -> IngestionJob:
        job = self.jobs[job_id]
        updated = replace(
            job,
            status=IngestionJobStatus.DEAD_LETTERED,
            last_error=error_message,
        )
        self.jobs[job_id] = updated
        return updated


class FakeCursorRepository:
    def __init__(self, *, advance_result: bool = True) -> None:
        self.advance_result = advance_result
        self.advance_calls: list[tuple[str, str, str, str | None, str]] = []

    def advance_cursor(
        self,
        *,
        source: str,
        dataset: str,
        checkpoint_key: str,
        cursor: str,
        expected_cursor: str | None,
    ) -> bool:
        self.advance_calls.append(
            (source, dataset, checkpoint_key, expected_cursor, cursor)
        )
        return self.advance_result

    def get_cursor(
        self,
        *,
        source: str,
        dataset: str,
        checkpoint_key: str,
    ) -> str | None:
        del source, dataset, checkpoint_key
        return None


class FakeHandler:
    source_name = "polymarket_gamma"
    dataset_name = "markets"

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        record = build_raw_record(
            source=job.source,
            dataset=job.dataset,
            job_id=job.job_id,
            endpoint="https://gamma-api.polymarket.com/markets",
            request_params=dict(job.params),
            payload=[{"id": "market-1"}],
            cursor=job.cursor,
        )
        return IngestionBatch(
            source=job.source,
            dataset=job.dataset,
            job_id=job.job_id,
            records=[record],
            next_cursor="offset=1",
            has_more=True,
        )


class SnapshotHandler(FakeHandler):
    def fetch(self, job: IngestionJob) -> IngestionBatch:
        batch = super().fetch(job)
        return replace(batch, next_cursor=None, has_more=False)


class FailingHandler:
    source_name = "polymarket_gamma"
    dataset_name = "markets"

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        del job
        raise RuntimeError("boom")


class FailingService:
    def run_job(self, job_id: str, *, worker_id: str) -> None:
        del job_id, worker_id
        raise RuntimeError("boom")


def build_service(
    tmp_path: Path,
    handlers,
    *,
    advance_result: bool = True,
    retry_settings: RetrySettings | None = None,
) -> tuple[IngestionService, FakeJobRepository, FakeCursorRepository, FakeJobQueue]:
    job_repository = FakeJobRepository()
    cursor_repository = FakeCursorRepository(advance_result=advance_result)
    queue = FakeJobQueue()
    service = IngestionService(
        job_repository=job_repository,
        cursor_repository=cursor_repository,
        source_registry=build_registry(handlers),
        raw_storage=RawBatchStorage(
            object_store=LocalFilesystemObjectStore(root_directory=tmp_path),
            container_name="raw",
        ),
        retry_settings=retry_settings or RetrySettings(),
        job_queue=queue,
    )
    return service, job_repository, cursor_repository, queue


def test_submit_request_persists_job_and_publishes_job_id(tmp_path: Path) -> None:
    service, job_repository, _cursor_repository, queue = build_service(tmp_path, [FakeHandler()])

    job = service.submit_request(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "mode": "snapshot"},
            trigger="test",
        )
    )

    assert job_repository.get_job(job.job_id) is not None
    assert queue.published_job_ids == [job.job_id]


def test_submit_request_does_not_republish_existing_idempotent_job(tmp_path: Path) -> None:
    service, _job_repository, _cursor_repository, queue = build_service(tmp_path, [FakeHandler()])

    first_job = service.submit_request(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "mode": "snapshot"},
            trigger="test",
            idempotency_key="same-request",
        )
    )
    second_job = service.submit_request(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "mode": "snapshot"},
            trigger="test",
            idempotency_key="same-request",
        )
    )

    assert first_job.job_id == second_job.job_id
    assert queue.published_job_ids == [first_job.job_id]


def test_run_job_advances_checkpoint_cursor_when_owner_is_present(tmp_path: Path) -> None:
    service, job_repository, cursor_repository, _queue = build_service(tmp_path, [FakeHandler()])
    job = job_repository.create_job(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "mode": "backfill", "offset": 0},
            cursor="offset=0",
            checkpoint_key="schedule:markets",
        )
    )

    artifact = service.run_job(job.job_id, worker_id="worker-1")

    updated_job = job_repository.get_job(job.job_id)
    assert artifact.next_cursor == "offset=1"
    assert updated_job is not None
    assert updated_job.status == IngestionJobStatus.SUCCEEDED
    assert cursor_repository.advance_calls == [
        ("polymarket_gamma", "markets", "schedule:markets", "offset=0", "offset=1")
    ]


def test_run_job_does_not_advance_cursor_without_checkpoint_owner(tmp_path: Path) -> None:
    service, job_repository, cursor_repository, _queue = build_service(
        tmp_path,
        [SnapshotHandler()],
    )
    job = job_repository.create_job(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "mode": "snapshot"},
        )
    )

    artifact = service.run_job(job.job_id, worker_id="worker-1")

    assert artifact.next_cursor is None
    assert cursor_repository.advance_calls == []


def test_run_job_fails_on_stale_cursor_update(tmp_path: Path) -> None:
    service, job_repository, cursor_repository, _queue = build_service(
        tmp_path,
        [FakeHandler()],
        advance_result=False,
    )
    job = job_repository.create_job(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "mode": "backfill", "offset": 0},
            cursor="offset=0",
            checkpoint_key="schedule:markets",
        )
    )

    try:
        service.run_job(job.job_id, worker_id="worker-1")
    except StaleCursorUpdateError:
        pass
    else:
        raise AssertionError("expected stale cursor update failure")

    updated_job = job_repository.get_job(job.job_id)
    assert updated_job is not None
    assert updated_job.status == IngestionJobStatus.FAILED
    assert cursor_repository.advance_calls == [
        ("polymarket_gamma", "markets", "schedule:markets", "offset=0", "offset=1")
    ]


def test_run_job_schedules_retry_after_failure(tmp_path: Path) -> None:
    service, job_repository, _cursor_repository, queue = build_service(
        tmp_path,
        [FailingHandler()],
        retry_settings=RetrySettings(
            max_attempts=3,
            base_delay_seconds=0,
            max_delay_seconds=0,
        ),
    )
    job = job_repository.create_job(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "mode": "snapshot"},
        )
    )

    try:
        service.run_job(job.job_id, worker_id="worker-1")
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("expected runtime error")

    updated_job = job_repository.get_job(job.job_id)
    assert updated_job is not None
    assert updated_job.status == IngestionJobStatus.RETRY_PENDING
    assert updated_job.attempts == 1
    assert updated_job.queued_at is not None
    assert queue.published_job_ids == [job.job_id]


def test_run_job_dead_letters_after_max_attempts(tmp_path: Path) -> None:
    service, job_repository, _cursor_repository, queue = build_service(
        tmp_path,
        [FailingHandler()],
        retry_settings=RetrySettings(
            max_attempts=1,
            base_delay_seconds=0,
            max_delay_seconds=0,
        ),
    )
    job = job_repository.create_job(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "mode": "snapshot"},
        )
    )

    try:
        service.run_job(job.job_id, worker_id="worker-1")
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("expected runtime error")

    updated_job = job_repository.get_job(job.job_id)
    assert updated_job is not None
    assert updated_job.status == IngestionJobStatus.DEAD_LETTERED
    assert queue.published_job_ids == []


def test_worker_consumer_swallows_service_failures() -> None:
    queue = FakeJobQueue()
    consumer = IngestionWorkerConsumer(
        job_queue=queue,
        ingestion_service=FailingService(),  # type: ignore[arg-type]
        worker_id="worker-1",
    )

    consumer.process_job_id("job-1")
