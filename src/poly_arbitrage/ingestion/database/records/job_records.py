from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, insert, select, update
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.exc import IntegrityError

from poly_arbitrage.ingestion.database.records.datetimes import ensure_utc_datetime
from poly_arbitrage.ingestion.database.tables import INGESTION_JOBS_TABLE


@dataclass(frozen=True, slots=True)
class IngestionJobRecord:
    job_id: str
    source: str
    dataset: str
    params: dict[str, object]
    cursor: str | None
    checkpoint_key: str | None
    trigger: str
    requested_at: datetime
    available_at: datetime
    status: str
    attempts: int
    worker_id: str | None
    queued_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    last_error: str | None
    idempotency_key: str | None
    batch_id: str | None
    object_uri: str | None
    record_count: int | None
    next_cursor: str | None
    has_more: bool
    source_watermark: str | None


class IngestionJobRecordStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def save(self, record: IngestionJobRecord) -> IngestionJobRecord:
        existing = self.get(record.job_id)
        try:
            with self.engine.begin() as connection:
                if existing is None:
                    connection.execute(insert(INGESTION_JOBS_TABLE).values(self._payload(record)))
                else:
                    connection.execute(
                        update(INGESTION_JOBS_TABLE)
                        .where(INGESTION_JOBS_TABLE.c.job_id == record.job_id)
                        .values(self._payload(record))
                    )
        except IntegrityError:
            if existing is None and record.idempotency_key is not None:
                loaded = self.get_by_idempotency_key(
                    source=record.source,
                    dataset=record.dataset,
                    idempotency_key=record.idempotency_key,
                )
                if loaded is not None:
                    return loaded
            raise
        loaded = self.get(record.job_id)
        if loaded is None:
            raise KeyError(f"unknown job_id={record.job_id!r}")
        return loaded

    def get(self, job_id: str) -> IngestionJobRecord | None:
        query = select(INGESTION_JOBS_TABLE).where(INGESTION_JOBS_TABLE.c.job_id == job_id)
        with self.engine.begin() as connection:
            row = connection.execute(query).mappings().first()
        if row is None:
            return None
        return self._from_row(row)

    def get_by_idempotency_key(
        self,
        *,
        source: str,
        dataset: str,
        idempotency_key: str,
    ) -> IngestionJobRecord | None:
        query = select(INGESTION_JOBS_TABLE).where(
            and_(
                INGESTION_JOBS_TABLE.c.source == source,
                INGESTION_JOBS_TABLE.c.dataset == dataset,
                INGESTION_JOBS_TABLE.c.idempotency_key == idempotency_key,
            )
        )
        with self.engine.begin() as connection:
            row = connection.execute(query).mappings().first()
        if row is None:
            return None
        return self._from_row(row)

    def list(
        self,
        *,
        status: str | None = None,
        source: str | None = None,
        dataset: str | None = None,
        limit: int = 100,
    ) -> list[IngestionJobRecord]:
        conditions = []
        if status is not None:
            conditions.append(INGESTION_JOBS_TABLE.c.status == status)
        if source is not None:
            conditions.append(INGESTION_JOBS_TABLE.c.source == source)
        if dataset is not None:
            conditions.append(INGESTION_JOBS_TABLE.c.dataset == dataset)

        query = select(INGESTION_JOBS_TABLE)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(INGESTION_JOBS_TABLE.c.requested_at.desc()).limit(limit)

        with self.engine.begin() as connection:
            rows = connection.execute(query).mappings().all()
        return [self._from_row(row) for row in rows]

    def list_retry_ready(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[IngestionJobRecord]:
        query = (
            select(INGESTION_JOBS_TABLE)
            .where(
                and_(
                    INGESTION_JOBS_TABLE.c.status == "retry_pending",
                    INGESTION_JOBS_TABLE.c.available_at <= now,
                    INGESTION_JOBS_TABLE.c.queued_at.is_(None),
                )
            )
            .order_by(INGESTION_JOBS_TABLE.c.available_at.asc())
            .limit(limit)
        )
        with self.engine.begin() as connection:
            rows = connection.execute(query).mappings().all()
        return [self._from_row(row) for row in rows]

    def delete(self, record: IngestionJobRecord) -> None:
        query = INGESTION_JOBS_TABLE.delete().where(INGESTION_JOBS_TABLE.c.job_id == record.job_id)
        with self.engine.begin() as connection:
            connection.execute(query)

    def _payload(self, record: IngestionJobRecord) -> dict[str, object]:
        return {
            "job_id": record.job_id,
            "source": record.source,
            "dataset": record.dataset,
            "params": dict(record.params),
            "cursor": record.cursor,
            "checkpoint_key": record.checkpoint_key,
            "trigger": record.trigger,
            "requested_at": record.requested_at,
            "available_at": record.available_at,
            "status": record.status,
            "attempts": record.attempts,
            "worker_id": record.worker_id,
            "queued_at": record.queued_at,
            "started_at": record.started_at,
            "completed_at": record.completed_at,
            "last_error": record.last_error,
            "idempotency_key": record.idempotency_key,
            "batch_id": record.batch_id,
            "object_uri": record.object_uri,
            "record_count": record.record_count,
            "next_cursor": record.next_cursor,
            "has_more": record.has_more,
            "source_watermark": record.source_watermark,
        }

    def _from_row(self, row: RowMapping) -> IngestionJobRecord:
        return IngestionJobRecord(
            job_id=str(row["job_id"]),
            source=str(row["source"]),
            dataset=str(row["dataset"]),
            params=dict(row["params"] or {}),
            cursor=self._optional_str(row.get("cursor")),
            checkpoint_key=self._optional_str(row.get("checkpoint_key")),
            trigger=str(row["trigger"]),
            requested_at=self._as_datetime(row["requested_at"]),
            available_at=self._as_datetime(row["available_at"]),
            status=str(row["status"]),
            attempts=int(row["attempts"]),
            worker_id=self._optional_str(row.get("worker_id")),
            queued_at=self._optional_datetime(row.get("queued_at")),
            started_at=self._optional_datetime(row.get("started_at")),
            completed_at=self._optional_datetime(row.get("completed_at")),
            last_error=self._optional_str(row.get("last_error")),
            idempotency_key=self._optional_str(row.get("idempotency_key")),
            batch_id=self._optional_str(row.get("batch_id")),
            object_uri=self._optional_str(row.get("object_uri")),
            record_count=self._optional_int(row.get("record_count")),
            next_cursor=self._optional_str(row.get("next_cursor")),
            has_more=bool(row["has_more"]),
            source_watermark=self._optional_str(row.get("source_watermark")),
        )

    def _as_datetime(self, value: object) -> datetime:
        return ensure_utc_datetime(value)

    def _optional_datetime(self, value: object) -> datetime | None:
        if value is None:
            return None
        return self._as_datetime(value)

    def _optional_str(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    def _optional_int(self, value: object) -> int | None:
        if value is None:
            return None
        return int(value)
