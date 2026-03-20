from __future__ import annotations

from dataclasses import dataclass

from poly_arbitrage.ingestion.database.registry import RepositoryRegistry
from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(slots=True)
class CursorRepository:
    registry: RepositoryRegistry

    def advance_cursor(
        self,
        *,
        source: str,
        dataset: str,
        checkpoint_key: str,
        cursor: str,
        expected_cursor: str | None,
    ) -> bool:
        return self.registry.cursor_records.compare_and_set(
            source=source,
            dataset=dataset,
            checkpoint_key=checkpoint_key,
            expected_cursor=expected_cursor,
            next_cursor=cursor,
            updated_at=utc_now(),
        )

    def get_cursor(
        self,
        *,
        source: str,
        dataset: str,
        checkpoint_key: str,
    ) -> str | None:
        record = self.registry.cursor_records.get(
            source=source,
            dataset=dataset,
            checkpoint_key=checkpoint_key,
        )
        return None if record is None else record.cursor
