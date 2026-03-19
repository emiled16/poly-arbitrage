from __future__ import annotations

from dataclasses import dataclass

from poly_arbitrage.ingestion.models.manifest import IngestionBatchManifest, ProcessedIngestionJob
from poly_arbitrage.ingestion.protocols.ingestion_job_queue import IngestionJobQueue
from poly_arbitrage.ingestion.protocols.ingestion_state_store import IngestionStateStore
from poly_arbitrage.ingestion.protocols.raw_sink import RawSink
from poly_arbitrage.ingestion.protocols.source_connector import SourceConnector


@dataclass(slots=True)
class IngestionWorker:
    connectors: dict[tuple[str, str], SourceConnector]
    job_queue: IngestionJobQueue
    raw_sink: RawSink
    state_store: IngestionStateStore

    def process_next(self) -> ProcessedIngestionJob | None:
        job = self.job_queue.dequeue()
        if job is None:
            return None

        connector = self._get_connector(job.source, job.dataset)

        try:
            batch = connector.fetch(job)
            object_uri = self.raw_sink.write_batch(batch)
            manifest = IngestionBatchManifest(
                batch_id=batch.batch_id,
                job_id=job.job_id,
                source=job.source,
                dataset=job.dataset,
                object_uri=object_uri,
                record_count=len(batch.records),
                next_cursor=batch.next_cursor,
            )
            self.state_store.record_success(job, manifest)
        except Exception as exc:
            self.state_store.record_failure(job, str(exc))
            raise

        return ProcessedIngestionJob(job=job, manifest=manifest)

    def _get_connector(self, source: str, dataset: str) -> SourceConnector:
        key = (source, dataset)
        if key not in self.connectors:
            raise KeyError(f"no connector registered for source={source!r}, dataset={dataset!r}")
        return self.connectors[key]
