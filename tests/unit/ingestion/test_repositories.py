from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from poly_arbitrage.ingestion.models.artifact import IngestionArtifact
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.models.schedule import IngestionSchedule
from poly_arbitrage.ingestion.submission import build_schedule_checkpoint_key
from poly_arbitrage.ingestion.utils.clock import utc_now


def build_repositories():
    sqlalchemy = pytest.importorskip("sqlalchemy")
    from poly_arbitrage.ingestion.database.database import IngestionDatabase
    from poly_arbitrage.ingestion.database.registry import RepositoryRegistry
    from poly_arbitrage.ingestion.repositories.cursors import CursorRepository
    from poly_arbitrage.ingestion.repositories.jobs import JobRepository
    from poly_arbitrage.ingestion.repositories.schedules import ScheduleRepository

    engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:", future=True)
    database = IngestionDatabase(engine=engine)
    database.create_schema()
    registry = RepositoryRegistry(
        job_records=database.jobs,
        cursor_records=database.cursors,
        schedule_records=database.schedules,
    )
    return (
        JobRepository(registry=registry),
        CursorRepository(registry=registry),
        ScheduleRepository(registry=registry),
    )


def test_repositories_persist_job_lifecycle_and_owner_scoped_cursor() -> None:
    job_repository, cursor_repository, _schedule_repository = build_repositories()
    request = IngestionRequest(
        source="polymarket_gamma",
        dataset="markets",
        params={"limit": 100, "mode": "backfill", "offset": 0},
        cursor="offset=0",
        checkpoint_key="schedule:markets",
        trigger="test",
    )

    job = job_repository.create_job(request)
    job_repository.mark_running(job.job_id, worker_id="worker-1")
    job_repository.mark_succeeded(
        job.job_id,
        IngestionArtifact(
            batch_id="batch-1",
            job_id=job.job_id,
            source="polymarket_gamma",
            dataset="markets",
            object_uri="s3://raw/batch-1.jsonl",
            record_count=1,
            next_cursor="offset=100",
            has_more=True,
        ),
    )
    advanced = cursor_repository.advance_cursor(
        source="polymarket_gamma",
        dataset="markets",
        checkpoint_key="schedule:markets",
        expected_cursor="offset=0",
        cursor="offset=100",
    )

    loaded_job = job_repository.get_job(job.job_id)

    assert advanced is True
    assert loaded_job is not None
    assert loaded_job.checkpoint_key == "schedule:markets"
    assert (
        cursor_repository.get_cursor(
            source="polymarket_gamma",
            dataset="markets",
            checkpoint_key="schedule:markets",
        )
        == "offset=100"
    )


def test_cursor_repository_isolates_checkpoints_by_owner() -> None:
    _job_repository, cursor_repository, _schedule_repository = build_repositories()

    first = cursor_repository.advance_cursor(
        source="polymarket_gamma",
        dataset="markets",
        checkpoint_key="schedule:one",
        expected_cursor=None,
        cursor="offset=100",
    )
    second = cursor_repository.advance_cursor(
        source="polymarket_gamma",
        dataset="markets",
        checkpoint_key="backfill:manual",
        expected_cursor=None,
        cursor="offset=500",
    )

    assert first is True
    assert second is True
    assert (
        cursor_repository.get_cursor(
            source="polymarket_gamma",
            dataset="markets",
            checkpoint_key="schedule:one",
        )
        == "offset=100"
    )
    assert (
        cursor_repository.get_cursor(
            source="polymarket_gamma",
            dataset="markets",
            checkpoint_key="backfill:manual",
        )
        == "offset=500"
    )


def test_cursor_repository_rejects_stale_updates() -> None:
    _job_repository, cursor_repository, _schedule_repository = build_repositories()

    created = cursor_repository.advance_cursor(
        source="polymarket_gamma",
        dataset="markets",
        checkpoint_key="schedule:markets",
        expected_cursor=None,
        cursor="offset=100",
    )
    stale = cursor_repository.advance_cursor(
        source="polymarket_gamma",
        dataset="markets",
        checkpoint_key="schedule:markets",
        expected_cursor="offset=50",
        cursor="offset=200",
    )

    assert created is True
    assert stale is False
    assert (
        cursor_repository.get_cursor(
            source="polymarket_gamma",
            dataset="markets",
            checkpoint_key="schedule:markets",
        )
        == "offset=100"
    )


def test_repositories_enforce_idempotency_key_per_source_and_dataset() -> None:
    job_repository, _cursor_repository, _schedule_repository = build_repositories()
    request = IngestionRequest(
        source="polymarket_gamma",
        dataset="markets",
        params={"limit": 100, "mode": "snapshot"},
        trigger="test",
        idempotency_key="same-request",
    )

    first_job = job_repository.create_job(request)
    second_job = job_repository.create_job(request)

    assert first_job.job_id == second_job.job_id
    assert len(job_repository.list_jobs(limit=10)) == 1


def test_schedule_claiming_is_atomic_and_advances_next_run_at() -> None:
    _job_repository, _cursor_repository, schedule_repository = build_repositories()
    now = utc_now()
    schedule = IngestionSchedule(
        schedule_id=uuid4().hex,
        name="gamma-markets",
        source="polymarket_gamma",
        dataset="markets",
        cadence_seconds=60,
        params={"limit": 100, "mode": "snapshot"},
        next_run_at=now,
    )

    created = schedule_repository.create_schedule(schedule)
    claimed = schedule_repository.claim_due_schedules(
        now=now + timedelta(seconds=1),
        limit=10,
    )
    claimed_again = schedule_repository.claim_due_schedules(
        now=now + timedelta(seconds=1),
        limit=10,
    )

    assert created.schedule_id == schedule.schedule_id
    assert claimed[0].schedule.schedule_id == schedule.schedule_id
    assert claimed[0].due_at == now
    assert claimed[0].schedule.last_enqueued_at == now + timedelta(seconds=1)
    assert claimed[0].schedule.next_run_at == now + timedelta(seconds=60)
    assert claimed_again == []


def test_schedule_checkpoint_key_is_schedule_scoped() -> None:
    _job_repository, _cursor_repository, schedule_repository = build_repositories()
    schedule = schedule_repository.create_schedule(
        IngestionSchedule(
            schedule_id=uuid4().hex,
            name="gamma-markets",
            source="polymarket_gamma",
            dataset="markets",
            cadence_seconds=60,
            params={"limit": 100, "mode": "snapshot"},
        )
    )

    checkpoint_key = build_schedule_checkpoint_key(schedule)

    assert checkpoint_key == f"schedule:{schedule.schedule_id}"
