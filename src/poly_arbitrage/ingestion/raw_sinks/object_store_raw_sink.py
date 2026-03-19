from __future__ import annotations

from dataclasses import dataclass

from poly_arbitrage.ingestion.archive.batch_archive_layout import (
    build_raw_batch_object_key,
    build_raw_batch_object_metadata,
)
from poly_arbitrage.ingestion.archive.jsonl_batch_serializer import serialize_batch_to_jsonl_bytes
from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.protocols.object_store import ObjectStore


@dataclass(slots=True)
class ObjectStoreRawSink:
    object_store: ObjectStore
    container_name: str

    def write_batch(self, batch: IngestionBatch) -> str:
        object_key = build_raw_batch_object_key(batch)
        return self.object_store.put_bytes(
            container_name=self.container_name,
            object_key=object_key,
            payload=serialize_batch_to_jsonl_bytes(batch),
            content_type="application/x-ndjson",
            metadata=build_raw_batch_object_metadata(batch),
        )

