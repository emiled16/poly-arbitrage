from __future__ import annotations

from datetime import UTC

from poly_arbitrage.ingestion.models.batch import IngestionBatch


def build_raw_batch_object_key(batch: IngestionBatch) -> str:
    emitted_at = batch.emitted_at.astimezone(UTC)
    return "/".join(
        [
            f"source={batch.source}",
            f"dataset={batch.dataset}",
            f"date={emitted_at:%Y-%m-%d}",
            f"hour={emitted_at:%H}",
            f"job_id={batch.job_id}",
            f"batch={batch.batch_id}.jsonl",
        ]
    )


def build_raw_batch_object_metadata(batch: IngestionBatch) -> dict[str, str]:
    metadata = {
        "batch_id": batch.batch_id,
        "job_id": batch.job_id,
        "source": batch.source,
        "dataset": batch.dataset,
        "record_count": str(len(batch.records)),
        "emitted_at": batch.emitted_at.astimezone(UTC).isoformat(),
        "has_more": str(batch.has_more).lower(),
    }
    if batch.next_cursor is not None:
        metadata["next_cursor"] = batch.next_cursor
    if batch.source_watermark is not None:
        metadata["source_watermark"] = batch.source_watermark
    return metadata
