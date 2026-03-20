from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from poly_arbitrage.ingestion.contracts import JobRepository, ScheduleRepository
from poly_arbitrage.ingestion.models.job_status import IngestionJobStatus
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.models.schedule import IngestionSchedule
from poly_arbitrage.ingestion.scheduler import IngestionScheduler
from poly_arbitrage.ingestion.service import IngestionService
from poly_arbitrage.ingestion.submission import validate_schedule
from poly_arbitrage.ingestion.utils.clock import utc_now


class SubmitJobPayload(BaseModel):
    source: str
    dataset: str
    params: dict[str, Any] = Field(default_factory=dict)
    cursor: str | None = None
    checkpoint_key: str | None = None
    trigger: str = "api"
    available_at: datetime | None = None
    idempotency_key: str | None = None


class CreateSchedulePayload(BaseModel):
    name: str
    source: str
    dataset: str
    cadence_seconds: int
    params: dict[str, Any] = Field(default_factory=dict)
    bootstrap_cursor: str | None = None
    cursor: str | None = None
    trigger: str = "schedule"
    next_run_at: datetime | None = None


class RedriveJobPayload(BaseModel):
    publish: bool = True


def build_ingestion_api(
    *,
    ingestion_service: IngestionService,
    scheduler: IngestionScheduler,
    job_repository: JobRepository,
    schedule_repository: ScheduleRepository,
) -> FastAPI:
    app = FastAPI(title="poly-arbitrage ingestion")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ingestion/jobs")
    def submit_job(payload: SubmitJobPayload) -> dict[str, Any]:
        try:
            job = ingestion_service.submit_request(
                IngestionRequest(
                    source=payload.source,
                    dataset=payload.dataset,
                    params=dict(payload.params),
                    cursor=payload.cursor,
                    checkpoint_key=payload.checkpoint_key,
                    trigger=payload.trigger,
                    idempotency_key=payload.idempotency_key,
                ),
                available_at=payload.available_at,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "job_id": job.job_id,
            "status": job.status.value,
        }

    @app.get("/ingestion/jobs")
    def list_jobs(
        status: str | None = None,
        source: str | None = None,
        dataset: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        parsed_status = None if status is None else IngestionJobStatus(status)
        jobs = job_repository.list_jobs(
            status=parsed_status,
            source=source,
            dataset=dataset,
            limit=limit,
        )
        return [
            {
                "job_id": job.job_id,
                "source": job.source,
                "dataset": job.dataset,
                "status": job.status.value,
                "checkpoint_key": job.checkpoint_key,
                "attempts": job.attempts,
                "queued_at": None if job.queued_at is None else job.queued_at.isoformat(),
                "available_at": job.available_at.isoformat(),
                "requested_at": job.requested_at.isoformat(),
                "completed_at": None
                if job.completed_at is None
                else job.completed_at.isoformat(),
                "last_error": job.last_error,
            }
            for job in jobs
        ]

    @app.get("/ingestion/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        job = job_repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return {
            "job_id": job.job_id,
            "source": job.source,
            "dataset": job.dataset,
            "status": job.status.value,
            "checkpoint_key": job.checkpoint_key,
            "attempts": job.attempts,
            "worker_id": job.worker_id,
            "queued_at": None if job.queued_at is None else job.queued_at.isoformat(),
            "available_at": job.available_at.isoformat(),
            "requested_at": job.requested_at.isoformat(),
            "started_at": None if job.started_at is None else job.started_at.isoformat(),
            "completed_at": None if job.completed_at is None else job.completed_at.isoformat(),
            "last_error": job.last_error,
            "idempotency_key": job.idempotency_key,
        }

    @app.post("/ingestion/jobs/{job_id}/redrive")
    def redrive_job(job_id: str, payload: RedriveJobPayload) -> dict[str, Any]:
        try:
            job = ingestion_service.redrive_job(job_id, publish=payload.publish)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc
        return {"job_id": job.job_id, "status": job.status.value}

    @app.post("/ingestion/schedules")
    def create_schedule(payload: CreateSchedulePayload) -> dict[str, str]:
        try:
            schedule = validate_schedule(
                IngestionSchedule(
                    schedule_id=uuid4().hex,
                    name=payload.name,
                    source=payload.source,
                    dataset=payload.dataset,
                    cadence_seconds=payload.cadence_seconds,
                    params=dict(payload.params),
                    bootstrap_cursor=payload.bootstrap_cursor or payload.cursor,
                    trigger=payload.trigger,
                    next_run_at=payload.next_run_at or utc_now(),
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        schedule = schedule_repository.create_schedule(schedule)
        return {"schedule_id": schedule.schedule_id}

    @app.post("/ingestion/schedules/run")
    def run_due_schedules() -> dict[str, list[str]]:
        return {"job_ids": scheduler.enqueue_due_schedules()}

    @app.get("/ingestion/schedules")
    def list_schedules(
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        schedules = schedule_repository.list_schedules(is_active=is_active, limit=limit)
        return [
            {
                "schedule_id": schedule.schedule_id,
                "name": schedule.name,
                "source": schedule.source,
                "dataset": schedule.dataset,
                "cadence_seconds": schedule.cadence_seconds,
                "bootstrap_cursor": schedule.bootstrap_cursor,
                "is_active": schedule.is_active,
                "next_run_at": schedule.next_run_at.isoformat(),
                "last_enqueued_at": None
                if schedule.last_enqueued_at is None
                else schedule.last_enqueued_at.isoformat(),
            }
            for schedule in schedules
        ]

    @app.post("/ingestion/admin/run")
    def run_due_work(limit: int = 100) -> dict[str, list[str]]:
        return scheduler.enqueue_due_work(limit=limit)

    return app
