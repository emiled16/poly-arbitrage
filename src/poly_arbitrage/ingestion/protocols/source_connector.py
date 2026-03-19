from __future__ import annotations

from typing import Protocol

from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.job import IngestionJob


class SourceConnector(Protocol):
    source_name: str
    dataset_name: str

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        """Fetch raw payloads for one source-specific ingestion job."""
