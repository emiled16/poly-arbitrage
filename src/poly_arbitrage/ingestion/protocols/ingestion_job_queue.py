from __future__ import annotations

from typing import Protocol

from poly_arbitrage.ingestion.models.job import IngestionJob


class IngestionJobQueue(Protocol):
    def enqueue(self, job: IngestionJob) -> None:
        """Add a job to the queue."""

    def dequeue(self) -> IngestionJob | None:
        """Get the next job from the queue."""
