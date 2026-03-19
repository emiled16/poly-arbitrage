from __future__ import annotations

from typing import Protocol

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.manifest import IngestionBatchManifest


class IngestionStateStore(Protocol):
    def record_success(self, job: IngestionJob, manifest: IngestionBatchManifest) -> None:
        """Persist a successful ingestion result."""

    def record_failure(self, job: IngestionJob, error_message: str) -> None:
        """Persist a failed ingestion result."""
