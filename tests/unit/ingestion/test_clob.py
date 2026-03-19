from __future__ import annotations

from datetime import UTC, datetime

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.sources.polymarket.connectors.clob_book_connector import (
    PolymarketClobBookConnector,
)
from poly_arbitrage.ingestion.sources.polymarket.connectors.clob_midpoint_connector import (
    PolymarketClobMidpointConnector,
)


class FakeHttpClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses

    def get_json(self, url: str, params: dict[str, object] | None = None) -> object:
        token_id = params["token_id"] if params else ""
        return self.responses[f"{url}?token_id={token_id}"]


def test_clob_book_connector_emits_raw_book_payload() -> None:
    connector = PolymarketClobBookConnector(
        http_client=FakeHttpClient(
            {
                "https://clob.polymarket.com/book?token_id=yes-token": {
                    "market": "condition-1",
                    "asset_id": "yes-token",
                    "timestamp": "1711320000",
                    "bids": [{"price": "0.55", "size": "100"}],
                    "asks": [{"price": "0.57", "size": "110"}],
                    "min_order_size": "1",
                    "tick_size": "0.01",
                    "last_trade_price": "0.56",
                },
            }
        )
    )
    job = IngestionJob(
        job_id="job-1",
        source="polymarket_clob",
        dataset="book",
        params={"token_id": "yes-token"},
        enqueued_at=datetime(2026, 3, 18, 12, 0, tzinfo=UTC),
    )

    batch = connector.fetch(job)

    assert len(batch.records) == 1
    record = batch.records[0]
    assert record.endpoint == "https://clob.polymarket.com/book"
    assert record.request_params["token_id"] == "yes-token"
    assert record.payload["market"] == "condition-1"
    assert record.metadata["response_shape"] == "object"
    assert record.metadata["token_id"] == "yes-token"


def test_clob_midpoint_connector_emits_raw_midpoint_payload() -> None:
    connector = PolymarketClobMidpointConnector(
        http_client=FakeHttpClient(
            {
                "https://clob.polymarket.com/midpoint?token_id=yes-token": {
                    "mid_price": "0.56"
                },
            }
        )
    )
    job = IngestionJob(
        job_id="job-2",
        source="polymarket_clob",
        dataset="midpoint",
        params={"token_id": "yes-token"},
        enqueued_at=datetime(2026, 3, 18, 12, 0, tzinfo=UTC),
    )

    batch = connector.fetch(job)

    assert len(batch.records) == 1
    record = batch.records[0]
    assert record.endpoint == "https://clob.polymarket.com/midpoint"
    assert record.payload["mid_price"] == "0.56"
