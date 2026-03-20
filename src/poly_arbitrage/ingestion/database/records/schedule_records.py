from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from sqlalchemy import and_, insert, select, update
from sqlalchemy.engine import Engine, RowMapping

from poly_arbitrage.ingestion.database.records.datetimes import ensure_utc_datetime
from poly_arbitrage.ingestion.database.tables import INGESTION_SCHEDULES_TABLE


@dataclass(frozen=True, slots=True)
class IngestionScheduleRecord:
    schedule_id: str
    name: str
    source: str
    dataset: str
    cadence_seconds: int
    params: dict[str, object]
    bootstrap_cursor: str | None
    trigger: str
    is_active: bool
    next_run_at: datetime
    last_enqueued_at: datetime | None


@dataclass(frozen=True, slots=True)
class ClaimedIngestionScheduleRecord:
    schedule: IngestionScheduleRecord
    due_at: datetime


class IngestionScheduleRecordStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def save(self, record: IngestionScheduleRecord) -> IngestionScheduleRecord:
        existing = self.get(record.schedule_id)
        with self.engine.begin() as connection:
            if existing is None:
                connection.execute(insert(INGESTION_SCHEDULES_TABLE).values(self._payload(record)))
            else:
                connection.execute(
                    update(INGESTION_SCHEDULES_TABLE)
                    .where(INGESTION_SCHEDULES_TABLE.c.schedule_id == record.schedule_id)
                    .values(self._payload(record))
                )
        loaded = self.get(record.schedule_id)
        if loaded is None:
            raise KeyError(f"unknown schedule_id={record.schedule_id!r}")
        return loaded

    def get(self, schedule_id: str) -> IngestionScheduleRecord | None:
        query = select(INGESTION_SCHEDULES_TABLE).where(
            INGESTION_SCHEDULES_TABLE.c.schedule_id == schedule_id
        )
        with self.engine.begin() as connection:
            row = connection.execute(query).mappings().first()
        if row is None:
            return None
        return self._from_row(row)

    def claim_due(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[ClaimedIngestionScheduleRecord]:
        query = (
            select(INGESTION_SCHEDULES_TABLE)
            .where(
                and_(
                    INGESTION_SCHEDULES_TABLE.c.is_active.is_(True),
                    INGESTION_SCHEDULES_TABLE.c.next_run_at <= now,
                )
            )
            .order_by(INGESTION_SCHEDULES_TABLE.c.next_run_at.asc())
            .limit(limit)
        )
        claimed: list[ClaimedIngestionScheduleRecord] = []
        with self.engine.begin() as connection:
            rows = connection.execute(query).mappings().all()
            for row in rows:
                schedule = self._from_row(row)
                due_at = schedule.next_run_at
                next_run_at = due_at + timedelta(seconds=schedule.cadence_seconds)
                result = connection.execute(
                    update(INGESTION_SCHEDULES_TABLE)
                    .where(
                        and_(
                            INGESTION_SCHEDULES_TABLE.c.schedule_id == schedule.schedule_id,
                            INGESTION_SCHEDULES_TABLE.c.is_active.is_(True),
                            INGESTION_SCHEDULES_TABLE.c.next_run_at == due_at,
                            INGESTION_SCHEDULES_TABLE.c.next_run_at <= now,
                        )
                    )
                    .values(next_run_at=next_run_at, last_enqueued_at=now)
                )
                if result.rowcount != 1:
                    continue
                claimed.append(
                    ClaimedIngestionScheduleRecord(
                        schedule=replace(
                            schedule,
                            next_run_at=next_run_at,
                            last_enqueued_at=now,
                        ),
                        due_at=due_at,
                    )
                )
        return claimed

    def list(
        self,
        *,
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[IngestionScheduleRecord]:
        query = select(INGESTION_SCHEDULES_TABLE)
        if is_active is not None:
            query = query.where(INGESTION_SCHEDULES_TABLE.c.is_active.is_(is_active))
        query = query.order_by(INGESTION_SCHEDULES_TABLE.c.next_run_at.asc()).limit(limit)
        with self.engine.begin() as connection:
            rows = connection.execute(query).mappings().all()
        return [self._from_row(row) for row in rows]

    def delete(self, record: IngestionScheduleRecord) -> None:
        query = INGESTION_SCHEDULES_TABLE.delete().where(
            INGESTION_SCHEDULES_TABLE.c.schedule_id == record.schedule_id
        )
        with self.engine.begin() as connection:
            connection.execute(query)

    def _payload(self, record: IngestionScheduleRecord) -> dict[str, object]:
        return {
            "schedule_id": record.schedule_id,
            "name": record.name,
            "source": record.source,
            "dataset": record.dataset,
            "cadence_seconds": record.cadence_seconds,
            "params": dict(record.params),
            "bootstrap_cursor": record.bootstrap_cursor,
            "trigger": record.trigger,
            "is_active": record.is_active,
            "next_run_at": record.next_run_at,
            "last_enqueued_at": record.last_enqueued_at,
        }

    def _from_row(self, row: RowMapping) -> IngestionScheduleRecord:
        last_enqueued_at = row.get("last_enqueued_at")
        return IngestionScheduleRecord(
            schedule_id=str(row["schedule_id"]),
            name=str(row["name"]),
            source=str(row["source"]),
            dataset=str(row["dataset"]),
            cadence_seconds=int(row["cadence_seconds"]),
            params=dict(row["params"] or {}),
            bootstrap_cursor=(
                None
                if row.get("bootstrap_cursor") is None
                else str(row["bootstrap_cursor"])
            ),
            trigger=str(row["trigger"]),
            is_active=bool(row["is_active"]),
            next_run_at=ensure_utc_datetime(row["next_run_at"]),
            last_enqueued_at=(
                None
                if last_enqueued_at is None
                else ensure_utc_datetime(last_enqueued_at)
            ),
        )
