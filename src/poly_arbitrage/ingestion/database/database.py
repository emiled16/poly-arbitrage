from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.engine import Engine

from poly_arbitrage.ingestion.database.metadata import INGESTION_METADATA
from poly_arbitrage.ingestion.database.records.cursor_records import (
    IngestionCursorRecordStore,
)
from poly_arbitrage.ingestion.database.records.job_records import IngestionJobRecordStore
from poly_arbitrage.ingestion.database.records.schedule_records import (
    IngestionScheduleRecordStore,
)


@dataclass(slots=True)
class IngestionDatabase:
    engine: Engine
    jobs: IngestionJobRecordStore = field(init=False)
    cursors: IngestionCursorRecordStore = field(init=False)
    schedules: IngestionScheduleRecordStore = field(init=False)

    def __post_init__(self) -> None:
        self.jobs = IngestionJobRecordStore(self.engine)
        self.cursors = IngestionCursorRecordStore(self.engine)
        self.schedules = IngestionScheduleRecordStore(self.engine)

    def create_schema(self) -> None:
        INGESTION_METADATA.create_all(self.engine)
