from __future__ import annotations

from poly_arbitrage.ingestion.dispatchers.ingestion_dispatcher import IngestionDispatcher
from poly_arbitrage.ingestion.factories.raw_record_factory import build_raw_record
from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.queues.in_memory_job_queue import InMemoryJobQueue
from poly_arbitrage.ingestion.raw_sinks.in_memory_raw_sink import InMemoryRawSink
from poly_arbitrage.ingestion.state_stores.in_memory_state_store import InMemoryStateStore
from poly_arbitrage.ingestion.workers.ingestion_worker import IngestionWorker


class FakeConnector:
    source_name = "polymarket_gamma"
    dataset_name = "markets"

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        record = build_raw_record(
            source=job.source,
            dataset=job.dataset,
            job_id=job.job_id,
            endpoint="https://gamma-api.polymarket.com/markets",
            request_params=dict(job.params),
            payload=[{"id": "market-1"}],
            cursor=job.cursor,
        )
        return IngestionBatch(
            source=job.source,
            dataset=job.dataset,
            job_id=job.job_id,
            records=[record],
            next_cursor="offset=1",
        )


def test_dispatcher_and_worker_process_one_raw_ingestion_job() -> None:
    queue = InMemoryJobQueue()
    sink = InMemoryRawSink()
    state_store = InMemoryStateStore()
    connectors = {("polymarket_gamma", "markets"): FakeConnector()}
    dispatcher = IngestionDispatcher(connectors=connectors, job_queue=queue)
    worker = IngestionWorker(
        connectors=connectors,
        job_queue=queue,
        raw_sink=sink,
        state_store=state_store,
    )

    job = dispatcher.dispatch(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "offset": 0},
        )
    )
    processed = worker.process_next()

    assert processed is not None
    assert processed.job.job_id == job.job_id
    assert processed.manifest.record_count == 1
    assert processed.manifest.next_cursor == "offset=1"
    assert processed.manifest.object_uri.startswith("memory://")
    assert len(state_store.successes) == 1
    assert not state_store.failures
    assert not queue.jobs
