from __future__ import annotations

from dataclasses import replace

import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from poly_arbitrage.ingestion.api import build_ingestion_api
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.job_status import IngestionJobStatus
from poly_arbitrage.ingestion.models.schedule import IngestionSchedule
from poly_arbitrage.ingestion.submission import normalize_request
from poly_arbitrage.ingestion.utils.clock import utc_now


class FakeJobRepository:
    def __init__(self) -> None:
        now = utc_now()
        self.jobs = {
            "job-1": IngestionJob(
                job_id="job-1",
                source="polymarket_gamma",
                dataset="markets",
                params={"limit": 1, "mode": "snapshot"},
                status=IngestionJobStatus.DEAD_LETTERED,
                attempts=3,
                available_at=now,
                requested_at=now,
                completed_at=now,
                last_error="boom",
            )
        }

    def get_job(self, job_id: str) -> IngestionJob | None:
        return self.jobs.get(job_id)

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


class FakeScheduleRepository:
    def __init__(self) -> None:
        self.schedules = [
            IngestionSchedule(
                schedule_id="schedule-1",
                name="gamma-markets",
                source="polymarket_gamma",
                dataset="markets",
                cadence_seconds=60,
                params={"limit": 100, "mode": "snapshot"},
                next_run_at=utc_now(),
            )
        ]

    def create_schedule(self, schedule: IngestionSchedule) -> IngestionSchedule:
        self.schedules.append(schedule)
        return schedule

    def list_schedules(
        self,
        *,
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[IngestionSchedule]:
        schedules = list(self.schedules)
        if is_active is not None:
            schedules = [schedule for schedule in schedules if schedule.is_active == is_active]
        return schedules[:limit]


class FakeIngestionService:
    def __init__(self, job_repository: FakeJobRepository) -> None:
        self.job_repository = job_repository

    def submit_request(self, request, *, available_at=None, publish: bool = True):
        del available_at, publish
        normalize_request(request)
        return self.job_repository.jobs["job-1"]

    def redrive_job(self, job_id: str, *, publish: bool = True):
        del publish
        job = self.job_repository.jobs[job_id]
        new_job = replace(
            job,
            job_id="job-2",
            status=IngestionJobStatus.PENDING,
            attempts=0,
            completed_at=None,
            last_error=None,
        )
        self.job_repository.jobs[new_job.job_id] = new_job
        return new_job


class FakeScheduler:
    def enqueue_due_schedules(self, *, limit: int = 100) -> list[str]:
        del limit
        return ["job-scheduled-1"]

    def enqueue_due_work(self, *, limit: int = 100) -> dict[str, list[str]]:
        del limit
        return {
            "scheduled_job_ids": ["job-scheduled-1"],
            "retry_job_ids": ["job-retry-1"],
        }


def build_client() -> TestClient:
    job_repository = FakeJobRepository()
    return TestClient(
        build_ingestion_api(
            ingestion_service=FakeIngestionService(job_repository),  # type: ignore[arg-type]
            scheduler=FakeScheduler(),  # type: ignore[arg-type]
            job_repository=job_repository,  # type: ignore[arg-type]
            schedule_repository=FakeScheduleRepository(),  # type: ignore[arg-type]
        )
    )


def test_api_lists_jobs_and_schedules() -> None:
    client = build_client()

    jobs_response = client.get("/ingestion/jobs", params={"status": "dead_lettered"})
    schedules_response = client.get("/ingestion/schedules")

    assert jobs_response.status_code == 200
    assert jobs_response.json()[0]["job_id"] == "job-1"
    assert jobs_response.json()[0]["status"] == "dead_lettered"
    assert schedules_response.status_code == 200
    assert schedules_response.json()[0]["schedule_id"] == "schedule-1"


def test_api_redrives_jobs_and_runs_due_work() -> None:
    client = build_client()

    redrive_response = client.post("/ingestion/jobs/job-1/redrive", json={"publish": True})
    due_work_response = client.post("/ingestion/admin/run")

    assert redrive_response.status_code == 200
    assert redrive_response.json() == {"job_id": "job-2", "status": "pending"}
    assert due_work_response.status_code == 200
    assert due_work_response.json() == {
        "scheduled_job_ids": ["job-scheduled-1"],
        "retry_job_ids": ["job-retry-1"],
    }


def test_api_rejects_invalid_gamma_submission_defaults() -> None:
    client = build_client()

    response = client.post(
        "/ingestion/jobs",
        json={
            "source": "polymarket_gamma",
            "dataset": "markets",
            "params": {"limit": 100, "offset": 0},
        },
    )

    assert response.status_code == 400
    assert "offset" in response.json()["detail"]


def test_api_rejects_gamma_backfill_schedule_creation() -> None:
    client = build_client()

    response = client.post(
        "/ingestion/schedules",
        json={
            "name": "gamma-backfill",
            "source": "polymarket_gamma",
            "dataset": "markets",
            "cadence_seconds": 60,
            "params": {"limit": 100, "mode": "backfill", "offset": 0},
        },
    )

    assert response.status_code == 400
    assert "snapshot mode" in response.json()["detail"]
