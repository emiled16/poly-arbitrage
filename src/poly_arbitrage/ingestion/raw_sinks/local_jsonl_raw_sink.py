from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from pathlib import Path

from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.utils.serialization import stable_json_dumps


@dataclass(slots=True)
class LocalJsonlRawSink:
    root_directory: Path

    def write_batch(self, batch: IngestionBatch) -> str:
        emitted_at = batch.emitted_at.astimezone(UTC)
        path = (
            self.root_directory
            / f"source={batch.source}"
            / f"dataset={batch.dataset}"
            / f"date={emitted_at:%Y-%m-%d}"
            / f"hour={emitted_at:%H}"
            / f"{batch.batch_id}.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as handle:
            for record in batch.records:
                handle.write(stable_json_dumps(record))
                handle.write("\n")

        return str(path)
