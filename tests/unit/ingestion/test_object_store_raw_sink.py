from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.raw_record import build_raw_record
from poly_arbitrage.ingestion.object_stores.local import LocalFilesystemObjectStore
from poly_arbitrage.ingestion.raw_storage.raw_batch_storage import RawBatchStorage


def test_raw_batch_storage_writes_jsonl_batch_and_metadata(tmp_path: Path) -> None:
    batch = IngestionBatch(
        source="polymarket_gamma",
        dataset="markets",
        job_id="job-1",
        records=[
            build_raw_record(
                source="polymarket_gamma",
                dataset="markets",
                job_id="job-1",
                endpoint="https://gamma-api.polymarket.com/markets",
                request_params={"limit": 1, "offset": 0},
                payload=[{"id": "market-1"}],
            )
        ],
    )
    raw_storage = RawBatchStorage(
        object_store=LocalFilesystemObjectStore(root_directory=tmp_path),
        container_name="raw",
    )

    artifact = raw_storage.store_batch(batch)

    object_path = Path(unquote(urlparse(artifact.object_uri).path))
    assert object_path.exists()
    contents = object_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(contents) == 1
    serialized_record = json.loads(contents[0])
    assert serialized_record["source"] == "polymarket_gamma"
    assert serialized_record["payload"][0]["id"] == "market-1"

    metadata_path = object_path.with_name(f"{object_path.name}.metadata.json")
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["content_type"] == "application/x-ndjson"
    assert metadata["metadata"]["job_id"] == "job-1"
    assert metadata["metadata"]["source"] == "polymarket_gamma"
    assert artifact.record_count == 1
