from __future__ import annotations

from datetime import UTC, datetime

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.sources.polymarket.connectors.gamma_markets_connector import (
    PolymarketGammaMarketsConnector,
)


class FakeHttpClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def get_json(self, url: str, params: dict[str, object] | None = None) -> object:
        self.calls.append((url, params))
        return self.responses[url]


def test_gamma_connector_emits_raw_markets_batch() -> None:
    connector = PolymarketGammaMarketsConnector(
        http_client=FakeHttpClient(
            {
                "https://gamma-api.polymarket.com/markets": [
                    {
                        "id": "gamma-market-1",
                        "conditionId": "condition-1",
                        "question": "Will candidate X win?",
                        "slug": "candidate-x-win",
                        "description": "Binary outcome market",
                        "resolutionSource": "Official election result",
                        "category": "Politics",
                        "marketType": "binary",
                        "startDateIso": "2026-03-01T00:00:00Z",
                        "endDateIso": "2026-11-04T00:00:00Z",
                        "active": True,
                        "closed": False,
                        "archived": False,
                        "acceptingOrders": True,
                        "liquidityNum": 1212.5,
                        "volumeNum": 9123.25,
                        "volume24hr": 120.5,
                        "outcomes": "[\"Yes\", \"No\"]",
                        "outcomePrices": "[\"0.61\", \"0.39\"]",
                        "clobTokenIds": "[\"yes-token\", \"no-token\"]",
                    }
                ]
            }
        )
    )
    job = IngestionJob(
        job_id="job-1",
        source="polymarket_gamma",
        dataset="markets",
        params={"limit": 1, "offset": 0, "active": True, "closed": False},
        enqueued_at=datetime(2026, 3, 18, 12, 0, tzinfo=UTC),
    )

    batch = connector.fetch(job)

    assert batch.source == "polymarket_gamma"
    assert batch.dataset == "markets"
    assert batch.job_id == "job-1"
    assert batch.next_cursor == "offset=1"
    assert len(batch.records) == 1
    record = batch.records[0]
    assert record.endpoint == "https://gamma-api.polymarket.com/markets"
    assert record.request_params["limit"] == 1
    assert isinstance(record.payload, list)
    assert record.payload[0]["conditionId"] == "condition-1"
    assert record.metadata["response_shape"] == "list"
    assert record.metadata["item_count"] == 1
