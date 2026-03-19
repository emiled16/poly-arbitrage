from __future__ import annotations

from dataclasses import dataclass, field

from poly_arbitrage.ingestion.models.job import IngestionJob


@dataclass(slots=True)
class InMemoryJobQueue:
    jobs: list[IngestionJob] = field(default_factory=list)

    def enqueue(self, job: IngestionJob) -> None:
        self.jobs.append(job)

    def dequeue(self) -> IngestionJob | None:
        if not self.jobs:
            return None
        return self.jobs.pop(0)
