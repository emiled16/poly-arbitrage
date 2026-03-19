from __future__ import annotations

import pytest

from poly_arbitrage.ingestion.factories.job_factory import create_job
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


def test_worker_processes_one_raw_ingestion_job() -> None:
    queue = InMemoryJobQueue()
    sink = InMemoryRawSink()
    state_store = InMemoryStateStore()
    connectors = {("polymarket_gamma", "markets"): FakeConnector()}
    worker = IngestionWorker(
        connectors=connectors,
        job_queue=queue,
        raw_sink=sink,
        state_store=state_store,
    )

    job = create_job(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "offset": 0},
        )
    )
    queue.enqueue(job)
    processed = worker.process_next()

    assert processed is not None
    assert processed.job.job_id == job.job_id
    assert processed.manifest.record_count == 1
    assert processed.manifest.next_cursor == "offset=1"
    assert processed.manifest.object_uri.startswith("memory://")
    assert len(state_store.successes) == 1
    assert not state_store.failures
    assert not queue.jobs


def test_worker_records_failure_for_job_with_unregistered_connector() -> None:
    queue = InMemoryJobQueue()
    sink = InMemoryRawSink()
    state_store = InMemoryStateStore()

    job = create_job(
        IngestionRequest(
            source="polymarket_gamma",
            dataset="markets",
            params={"limit": 1, "offset": 0},
        )
    )
    queue.enqueue(job)

    worker = IngestionWorker(
        connectors={},
        job_queue=queue,
        raw_sink=sink,
        state_store=state_store,
    )

    with pytest.raises(KeyError, match="no connector registered"):
        worker.process_next()

    assert not state_store.successes
    assert len(state_store.failures) == 1
    assert state_store.failures[0].source == "polymarket_gamma"
    assert state_store.failures[0].dataset == "markets"
    assert not queue.jobs
