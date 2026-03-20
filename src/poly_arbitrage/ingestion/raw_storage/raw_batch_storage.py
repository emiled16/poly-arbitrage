from __future__ import annotations

from dataclasses import dataclass

from poly_arbitrage.ingestion.contracts import ObjectStore
from poly_arbitrage.ingestion.models.artifact import IngestionArtifact
from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.raw_storage.batch_storage_layout import (
    build_raw_batch_object_key,
    build_raw_batch_object_metadata,
)
from poly_arbitrage.ingestion.raw_storage.jsonl_batch_serializer import (
    serialize_batch_to_jsonl_bytes,
)


@dataclass(slots=True)
class RawBatchStorage:
    object_store: ObjectStore
    container_name: str

    def store_batch(self, batch: IngestionBatch) -> IngestionArtifact:
        object_key = build_raw_batch_object_key(batch)
        object_uri = self.object_store.put_bytes(
            container_name=self.container_name,
            object_key=object_key,
            payload=serialize_batch_to_jsonl_bytes(batch),
            content_type="application/x-ndjson",
            metadata=build_raw_batch_object_metadata(batch),
        )
        return IngestionArtifact(
            batch_id=batch.batch_id,
            job_id=batch.job_id,
            source=batch.source,
            dataset=batch.dataset,
            object_uri=object_uri,
            record_count=len(batch.records),
            next_cursor=batch.next_cursor,
            has_more=batch.has_more,
            source_watermark=batch.source_watermark,
        )
