from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poly_arbitrage.ingestion.database.records.cursor_records import (
    IngestionCursorRecord,
    IngestionCursorRecordStore,
)
from poly_arbitrage.ingestion.database.records.job_records import (
    IngestionJobRecord,
    IngestionJobRecordStore,
)
from poly_arbitrage.ingestion.database.records.schedule_records import (
    IngestionScheduleRecord,
    IngestionScheduleRecordStore,
)


@dataclass(slots=True)
class RepositoryRegistry:
    job_records: IngestionJobRecordStore
    cursor_records: IngestionCursorRecordStore
    schedule_records: IngestionScheduleRecordStore

    def save(
        self,
        record: IngestionJobRecord | IngestionCursorRecord | IngestionScheduleRecord,
    ) -> IngestionJobRecord | IngestionCursorRecord | IngestionScheduleRecord:
        repository = self.repo_for(type(record))
        return repository.save(record)

    def delete(
        self,
        record: IngestionJobRecord | IngestionCursorRecord | IngestionScheduleRecord,
    ) -> None:
        repository = self.repo_for(type(record))
        repository.delete(record)

    def repo_for(self, record_type: type[Any]) -> Any:
        mapping = {
            IngestionJobRecord: self.job_records,
            IngestionCursorRecord: self.cursor_records,
            IngestionScheduleRecord: self.schedule_records,
        }
        repository = mapping.get(record_type)
        if repository is None:
            raise KeyError(f"no repository registered for record_type={record_type!r}")
        return repository
