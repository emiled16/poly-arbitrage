from __future__ import annotations

from typing import Protocol

from poly_arbitrage.ingestion.models.batch import IngestionBatch


class RawSink(Protocol):
    def write_batch(self, batch: IngestionBatch) -> str:
        """Persist a raw batch and return its storage URI."""
