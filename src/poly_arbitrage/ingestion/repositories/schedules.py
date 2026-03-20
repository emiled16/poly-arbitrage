from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from poly_arbitrage.ingestion.database.records.schedule_records import (
    ClaimedIngestionScheduleRecord,
    IngestionScheduleRecord,
)
from poly_arbitrage.ingestion.database.registry import RepositoryRegistry
from poly_arbitrage.ingestion.models.schedule import ClaimedIngestionSchedule, IngestionSchedule


@dataclass(slots=True)
class ScheduleRepository:
    registry: RepositoryRegistry

    def create_schedule(self, schedule: IngestionSchedule) -> IngestionSchedule:
        record = IngestionScheduleRecord(
            schedule_id=schedule.schedule_id,
            name=schedule.name,
            source=schedule.source,
            dataset=schedule.dataset,
            cadence_seconds=schedule.cadence_seconds,
            params=dict(schedule.params),
            bootstrap_cursor=schedule.bootstrap_cursor,
            trigger=schedule.trigger,
            is_active=schedule.is_active,
            next_run_at=schedule.next_run_at,
            last_enqueued_at=schedule.last_enqueued_at,
        )
        return self._to_schedule(self.registry.save(record))

    def list_schedules(
        self,
        *,
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[IngestionSchedule]:
        return [
            self._to_schedule(record)
            for record in self.registry.schedule_records.list(
                is_active=is_active,
                limit=limit,
            )
        ]

    def claim_due_schedules(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[ClaimedIngestionSchedule]:
        return [
            self._to_claimed_schedule(record)
            for record in self.registry.schedule_records.claim_due(now=now, limit=limit)
        ]

    def _to_claimed_schedule(
        self,
        record: ClaimedIngestionScheduleRecord,
    ) -> ClaimedIngestionSchedule:
        return ClaimedIngestionSchedule(
            schedule=self._to_schedule(record.schedule),
            due_at=record.due_at,
        )

    def _to_schedule(
        self,
        record: IngestionScheduleRecord,
    ) -> IngestionSchedule:
        return IngestionSchedule(
            schedule_id=record.schedule_id,
            name=record.name,
            source=record.source,
            dataset=record.dataset,
            cadence_seconds=record.cadence_seconds,
            params=dict(record.params),
            bootstrap_cursor=record.bootstrap_cursor,
            trigger=record.trigger,
            is_active=record.is_active,
            next_run_at=record.next_run_at,
            last_enqueued_at=record.last_enqueued_at,
        )
