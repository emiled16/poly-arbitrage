from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.manifest import IngestionBatchManifest
from poly_arbitrage.ingestion.state_stores.local_jsonl_state_store import (
    LocalJsonlStateStore,
)


def test_local_jsonl_state_store_persists_success_and_failure_events(tmp_path: Path) -> None:
    store = LocalJsonlStateStore(root_directory=tmp_path)
    job = IngestionJob(
        job_id="job-1",
        source="polymarket_gamma",
        dataset="markets",
        params={"limit": 1},
        enqueued_at=datetime(2026, 3, 19, 5, 0, tzinfo=UTC),
    )
    manifest = IngestionBatchManifest(
        batch_id="batch-1",
        job_id=job.job_id,
        source=job.source,
        dataset=job.dataset,
        object_uri="file:///tmp/raw/batch-1.jsonl",
        record_count=1,
        next_cursor="offset=1",
    )

    store.record_success(job, manifest)
    store.record_failure(job, "boom")

    success_files = list(tmp_path.glob("success/date=*/hour=*/success.jsonl"))
    failure_files = list(tmp_path.glob("failure/date=*/hour=*/failure.jsonl"))
    assert len(success_files) == 1
    assert len(failure_files) == 1

    success_event = json.loads(success_files[0].read_text(encoding="utf-8").strip())
    failure_event = json.loads(failure_files[0].read_text(encoding="utf-8").strip())
    assert success_event["manifest"]["batch_id"] == "batch-1"
    assert success_event["job"]["job_id"] == "job-1"
    assert failure_event["job_id"] == "job-1"
    assert failure_event["error_message"] == "boom"

