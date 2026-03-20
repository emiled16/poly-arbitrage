from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, insert, select, update
from sqlalchemy.engine import Engine, RowMapping

from poly_arbitrage.ingestion.database.records.datetimes import ensure_utc_datetime
from poly_arbitrage.ingestion.database.tables import INGESTION_CURSORS_TABLE


@dataclass(frozen=True, slots=True)
class IngestionCursorRecord:
    source: str
    dataset: str
    checkpoint_key: str
    cursor: str
    updated_at: datetime


class IngestionCursorRecordStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get(
        self,
        *,
        source: str,
        dataset: str,
        checkpoint_key: str,
    ) -> IngestionCursorRecord | None:
        query = select(INGESTION_CURSORS_TABLE).where(
            and_(
                INGESTION_CURSORS_TABLE.c.source == source,
                INGESTION_CURSORS_TABLE.c.dataset == dataset,
                INGESTION_CURSORS_TABLE.c.checkpoint_key == checkpoint_key,
            )
        )
        with self.engine.begin() as connection:
            row = connection.execute(query).mappings().first()
        if row is None:
            return None
        return self._from_row(row)

    def save(self, record: IngestionCursorRecord) -> IngestionCursorRecord:
        with self.engine.begin() as connection:
            existing = (
                connection.execute(
                    select(INGESTION_CURSORS_TABLE).where(
                        and_(
                            INGESTION_CURSORS_TABLE.c.source == record.source,
                            INGESTION_CURSORS_TABLE.c.dataset == record.dataset,
                            INGESTION_CURSORS_TABLE.c.checkpoint_key == record.checkpoint_key,
                        )
                    )
                )
                .mappings()
                .first()
            )
            if existing is None:
                connection.execute(insert(INGESTION_CURSORS_TABLE).values(self._payload(record)))
            else:
                connection.execute(
                    update(INGESTION_CURSORS_TABLE)
                    .where(
                        and_(
                            INGESTION_CURSORS_TABLE.c.source == record.source,
                            INGESTION_CURSORS_TABLE.c.dataset == record.dataset,
                            INGESTION_CURSORS_TABLE.c.checkpoint_key == record.checkpoint_key,
                        )
                    )
                    .values(cursor=record.cursor, updated_at=record.updated_at)
                )
        loaded = self.get(
            source=record.source,
            dataset=record.dataset,
            checkpoint_key=record.checkpoint_key,
        )
        if loaded is None:
            raise KeyError(
                "unknown cursor record "
                f"source={record.source!r}, dataset={record.dataset!r}, "
                f"checkpoint_key={record.checkpoint_key!r}"
            )
        return loaded

    def compare_and_set(
        self,
        *,
        source: str,
        dataset: str,
        checkpoint_key: str,
        expected_cursor: str | None,
        next_cursor: str,
        updated_at: datetime,
    ) -> bool:
        with self.engine.begin() as connection:
            existing = (
                connection.execute(
                    select(INGESTION_CURSORS_TABLE).where(
                        and_(
                            INGESTION_CURSORS_TABLE.c.source == source,
                            INGESTION_CURSORS_TABLE.c.dataset == dataset,
                            INGESTION_CURSORS_TABLE.c.checkpoint_key == checkpoint_key,
                        )
                    )
                )
                .mappings()
                .first()
            )
            if existing is None:
                connection.execute(
                    insert(INGESTION_CURSORS_TABLE).values(
                        {
                            "source": source,
                            "dataset": dataset,
                            "checkpoint_key": checkpoint_key,
                            "cursor": next_cursor,
                            "updated_at": updated_at,
                        }
                    )
                )
                return True
            if expected_cursor is None:
                return False

            result = connection.execute(
                update(INGESTION_CURSORS_TABLE)
                .where(
                    and_(
                        INGESTION_CURSORS_TABLE.c.source == source,
                        INGESTION_CURSORS_TABLE.c.dataset == dataset,
                        INGESTION_CURSORS_TABLE.c.checkpoint_key == checkpoint_key,
                        INGESTION_CURSORS_TABLE.c.cursor == expected_cursor,
                    )
                )
                .values(cursor=next_cursor, updated_at=updated_at)
            )
        return bool(result.rowcount)

    def delete(self, record: IngestionCursorRecord) -> None:
        query = INGESTION_CURSORS_TABLE.delete().where(
            and_(
                INGESTION_CURSORS_TABLE.c.source == record.source,
                INGESTION_CURSORS_TABLE.c.dataset == record.dataset,
                INGESTION_CURSORS_TABLE.c.checkpoint_key == record.checkpoint_key,
            )
        )
        with self.engine.begin() as connection:
            connection.execute(query)

    def _payload(self, record: IngestionCursorRecord) -> dict[str, object]:
        return {
            "source": record.source,
            "dataset": record.dataset,
            "checkpoint_key": record.checkpoint_key,
            "cursor": record.cursor,
            "updated_at": record.updated_at,
        }

    def _from_row(self, row: RowMapping) -> IngestionCursorRecord:
        return IngestionCursorRecord(
            source=str(row["source"]),
            dataset=str(row["dataset"]),
            checkpoint_key=str(row["checkpoint_key"]),
            cursor=str(row["cursor"]),
            updated_at=ensure_utc_datetime(row["updated_at"]),
        )
