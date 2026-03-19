from __future__ import annotations

from dataclasses import dataclass, field

from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.sources.polymarket.connectors.clob_raw_batch_builder import (
    build_clob_batch,
)
from poly_arbitrage.ingestion.sources.polymarket.http.urllib_json_http_client import (
    UrllibJsonHttpClient,
)
from poly_arbitrage.ingestion.sources.polymarket.protocols.json_http_client import (
    JsonHttpClient,
)


@dataclass(slots=True)
class PolymarketClobBookConnector:
    http_client: JsonHttpClient = field(default_factory=UrllibJsonHttpClient)
    base_url: str = "https://clob.polymarket.com"
    source_name: str = "polymarket_clob"
    dataset_name: str = "book"

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        return build_clob_batch(
            http_client=self.http_client,
            base_url=self.base_url,
            source_name=self.source_name,
            dataset_name=self.dataset_name,
            job=job,
        )
