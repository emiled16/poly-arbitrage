from __future__ import annotations

from dataclasses import dataclass

from poly_arbitrage.ingestion.factories.job_factory import create_job
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.protocols.ingestion_job_queue import IngestionJobQueue
from poly_arbitrage.ingestion.protocols.source_connector import SourceConnector


@dataclass(slots=True)
class IngestionDispatcher:
    connectors: dict[tuple[str, str], SourceConnector]
    job_queue: IngestionJobQueue

    def dispatch(self, request: IngestionRequest) -> IngestionJob:
        self._get_connector(request.source, request.dataset)
        job = create_job(request)
        self.job_queue.enqueue(job)
        return job

    def _get_connector(self, source: str, dataset: str) -> SourceConnector:
        key = (source, dataset)
        if key not in self.connectors:
            raise KeyError(f"no connector registered for source={source!r}, dataset={dataset!r}")
        return self.connectors[key]
