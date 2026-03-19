from __future__ import annotations

from dataclasses import dataclass, field

from poly_arbitrage.ingestion.factories.raw_record_factory import build_raw_record
from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.sources.polymarket.connectors.gamma_markets_cursor import (
    next_offset_cursor,
    response_shape,
)
from poly_arbitrage.ingestion.sources.polymarket.http.urllib_json_http_client import (
    UrllibJsonHttpClient,
)
from poly_arbitrage.ingestion.sources.polymarket.protocols.json_http_client import (
    JsonHttpClient,
)


@dataclass(slots=True)
class PolymarketGammaMarketsConnector:
    http_client: JsonHttpClient = field(default_factory=UrllibJsonHttpClient)
    base_url: str = "https://gamma-api.polymarket.com"
    source_name: str = "polymarket_gamma"
    dataset_name: str = "markets"

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        payload = self.http_client.get_json(
            f"{self.base_url}/markets",
            params=job.params,
        )

        record = build_raw_record(
            source=self.source_name,
            dataset=self.dataset_name,
            job_id=job.job_id,
            endpoint=f"{self.base_url}/markets",
            request_params=dict(job.params),
            payload=payload,
            cursor=job.cursor,
            metadata={
                "response_shape": response_shape(payload),
                "item_count": len(payload) if isinstance(payload, list) else None,
            },
        )

        return IngestionBatch(
            source=self.source_name,
            dataset=self.dataset_name,
            job_id=job.job_id,
            records=[record],
            next_cursor=next_offset_cursor(job.params, payload),
        )
