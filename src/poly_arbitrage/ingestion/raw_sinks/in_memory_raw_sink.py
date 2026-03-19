from __future__ import annotations

from dataclasses import dataclass, field

from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.utils.serialization import stable_json_dumps


@dataclass(slots=True)
class InMemoryRawSink:
    batches_by_uri: dict[str, list[str]] = field(default_factory=dict)

    def write_batch(self, batch: IngestionBatch) -> str:
        uri = f"memory://{batch.source}/{batch.dataset}/{batch.batch_id}"
        self.batches_by_uri[uri] = [stable_json_dumps(record) for record in batch.records]
        return uri
