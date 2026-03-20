from __future__ import annotations

from uuid import uuid4

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.job_status import IngestionJobStatus
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.models.schedule import ClaimedIngestionSchedule, IngestionSchedule
from poly_arbitrage.ingestion.scheduler import IngestionScheduler
from poly_arbitrage.ingestion.utils.clock import utc_now


class FakeScheduleRepository:
    def __init__(self, claimed_schedules: list[ClaimedIngestionSchedule]) -> None:
        self.claimed_schedules = claimed_schedules

    def claim_due_schedules(self, *, now, limit: int = 100):
        del now, limit
        claimed, self.claimed_schedules = self.claimed_schedules, []
        return claimed


class FakeCursorRepository:
    def __init__(self, cursor: str | None) -> None:
        self.cursor = cursor
        self.lookups: list[tuple[str, str, str]] = []

    def get_cursor(self, *, source: str, dataset: str, checkpoint_key: str) -> str | None:
        self.lookups.append((source, dataset, checkpoint_key))
        return self.cursor


class FakeIngestionService:
    def __init__(self) -> None:
        self.requests: list[IngestionRequest] = []
        self.published_job_ids: list[str] = []

    def submit_request(self, request: IngestionRequest, *, available_at=None, publish: bool = True):
        del available_at, publish
        self.requests.append(request)
        return type("Job", (), {"job_id": "job-1"})()

    def publish_job(self, job_id: str):
        self.published_job_ids.append(job_id)
        return type("Job", (), {"job_id": job_id})()


class FakeJobRepository:
    def __init__(self, jobs: list[IngestionJob] | None = None) -> None:
        self.jobs = jobs or []

    def list_retry_ready(self, *, now, limit: int = 100) -> list[IngestionJob]:
        del now
        return self.jobs[:limit]


def test_scheduler_enqueues_due_schedule_using_schedule_checkpoint_owner() -> None:
    due_at = utc_now()
    schedule = IngestionSchedule(
        schedule_id=uuid4().hex,
        name="gamma-markets",
        source="polymarket_gamma",
        dataset="markets",
        cadence_seconds=60,
        params={"limit": 100, "mode": "snapshot"},
        next_run_at=due_at,
    )
    cursor_repository = FakeCursorRepository("offset=200")
    ingestion_service = FakeIngestionService()
    scheduler = IngestionScheduler(
        schedule_repository=FakeScheduleRepository(
            [ClaimedIngestionSchedule(schedule=schedule, due_at=due_at)]
        ),  # type: ignore[arg-type]
        job_repository=FakeJobRepository(),  # type: ignore[arg-type]
        cursor_repository=cursor_repository,  # type: ignore[arg-type]
        ingestion_service=ingestion_service,  # type: ignore[arg-type]
    )

    job_ids = scheduler.enqueue_due_schedules()

    assert job_ids == ["job-1"]
    assert cursor_repository.lookups == [
        ("polymarket_gamma", "markets", f"schedule:{schedule.schedule_id}")
    ]
    assert ingestion_service.requests[0].checkpoint_key == f"schedule:{schedule.schedule_id}"
    assert ingestion_service.requests[0].cursor == "offset=200"
    assert ingestion_service.requests[0].idempotency_key is not None
    assert schedule.schedule_id in ingestion_service.requests[0].idempotency_key


def test_scheduler_uses_bootstrap_cursor_when_no_persisted_cursor_exists() -> None:
    due_at = utc_now()
    schedule = IngestionSchedule(
        schedule_id=uuid4().hex,
        name="gamma-markets",
        source="polymarket_gamma",
        dataset="markets",
        cadence_seconds=60,
        params={"limit": 100, "mode": "snapshot"},
        bootstrap_cursor="offset=0",
        next_run_at=due_at,
    )
    scheduler = IngestionScheduler(
        schedule_repository=FakeScheduleRepository(
            [ClaimedIngestionSchedule(schedule=schedule, due_at=due_at)]
        ),  # type: ignore[arg-type]
        job_repository=FakeJobRepository(),  # type: ignore[arg-type]
        cursor_repository=FakeCursorRepository(None),  # type: ignore[arg-type]
        ingestion_service=FakeIngestionService(),  # type: ignore[arg-type]
    )

    scheduler.enqueue_due_schedules()

    assert scheduler.ingestion_service.requests[0].cursor == "offset=0"


def test_scheduler_enqueues_due_retries() -> None:
    ingestion_service = FakeIngestionService()
    scheduler = IngestionScheduler(
        schedule_repository=FakeScheduleRepository([]),  # type: ignore[arg-type]
        job_repository=FakeJobRepository(
            [
                IngestionJob(
                    job_id="job-retry-1",
                    source="polymarket_gamma",
                    dataset="markets",
                    params={},
                    status=IngestionJobStatus.RETRY_PENDING,
                )
            ]
        ),  # type: ignore[arg-type]
        cursor_repository=FakeCursorRepository(None),  # type: ignore[arg-type]
        ingestion_service=ingestion_service,  # type: ignore[arg-type]
    )

    job_ids = scheduler.enqueue_due_retries()

    assert job_ids == ["job-retry-1"]
    assert ingestion_service.published_job_ids == ["job-retry-1"]
