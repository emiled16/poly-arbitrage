from __future__ import annotations

import logging
from dataclasses import dataclass

from poly_arbitrage.ingestion.contracts import IngestionJobQueue
from poly_arbitrage.ingestion.service import IngestionService

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionWorkerConsumer:
    job_queue: IngestionJobQueue
    ingestion_service: IngestionService
    worker_id: str

    def run_forever(self) -> None:
        self.job_queue.consume(self.process_job_id)

    def process_job_id(self, job_id: str) -> None:
        try:
            self.ingestion_service.run_job(job_id, worker_id=self.worker_id)
        except Exception:
            LOGGER.exception("worker failed to process job", extra={"job_id": job_id})
