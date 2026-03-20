from __future__ import annotations

from dataclasses import dataclass

from poly_arbitrage.ingestion.contracts import CursorRepository, JobRepository, ScheduleRepository
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.service import IngestionService
from poly_arbitrage.ingestion.submission import (
    build_schedule_checkpoint_key,
    build_schedule_job_idempotency_key,
)
from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(slots=True)
class IngestionScheduler:
    schedule_repository: ScheduleRepository
    job_repository: JobRepository
    cursor_repository: CursorRepository
    ingestion_service: IngestionService

    def enqueue_due_schedules(self, *, limit: int = 100) -> list[str]:
        now = utc_now()
        scheduled_job_ids: list[str] = []
        schedules = self.schedule_repository.claim_due_schedules(now=now, limit=limit)
        for claimed_schedule in schedules:
            schedule = claimed_schedule.schedule
            checkpoint_key = build_schedule_checkpoint_key(schedule)
            persisted_cursor = self.cursor_repository.get_cursor(
                source=schedule.source,
                dataset=schedule.dataset,
                checkpoint_key=checkpoint_key,
            )
            cursor = persisted_cursor or schedule.bootstrap_cursor
            request = IngestionRequest(
                source=schedule.source,
                dataset=schedule.dataset,
                params=dict(schedule.params),
                cursor=cursor,
                checkpoint_key=checkpoint_key,
                trigger=schedule.trigger,
                idempotency_key=build_schedule_job_idempotency_key(
                    schedule,
                    due_at=claimed_schedule.due_at,
                ),
            )
            job = self.ingestion_service.submit_request(request)
            scheduled_job_ids.append(job.job_id)
        return scheduled_job_ids

    def enqueue_due_retries(self, *, limit: int = 100) -> list[str]:
        now = utc_now()
        published_job_ids: list[str] = []
        for job in self.job_repository.list_retry_ready(now=now, limit=limit):
            self.ingestion_service.publish_job(job.job_id)
            published_job_ids.append(job.job_id)
        return published_job_ids

    def enqueue_due_work(self, *, limit: int = 100) -> dict[str, list[str]]:
        return {
            "scheduled_job_ids": self.enqueue_due_schedules(limit=limit),
            "retry_job_ids": self.enqueue_due_retries(limit=limit),
        }
