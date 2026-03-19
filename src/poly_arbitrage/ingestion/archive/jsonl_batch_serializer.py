from __future__ import annotations

from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.utils.serialization import stable_json_dumps


def serialize_batch_to_jsonl_bytes(batch: IngestionBatch) -> bytes:
    lines = [stable_json_dumps(record) for record in batch.records]
    return ("\n".join(lines) + "\n").encode("utf-8")

