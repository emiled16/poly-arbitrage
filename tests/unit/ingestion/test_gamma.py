from __future__ import annotations

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.sources.polymarket.handlers import (
    GammaMarketsCheckpoint,
    PolymarketGammaMarketsHandler,
    format_gamma_markets_checkpoint,
    parse_iso_datetime,
)


class FakeHttpClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def get_json(self, url: str, params: dict[str, object] | None = None) -> object:
        self.calls.append((url, params))
        return self.responses[url]


def test_gamma_connector_uses_snapshot_mode_by_default() -> None:
    connector = PolymarketGammaMarketsHandler(
        http_client=FakeHttpClient(
            {
                "https://gamma-api.polymarket.com/markets": [
                    {
                        "id": "gamma-market-1",
                        "conditionId": "condition-1",
                        "question": "Will candidate X win?",
                        "updatedAt": "2026-03-20T00:00:00Z",
                    }
                ]
            }
        )
    )
    job = IngestionJob(
        job_id="job-1",
        source="polymarket_gamma",
        dataset="markets",
        params={"limit": 100, "active": True, "closed": False, "mode": "snapshot"},
    )

    batch = connector.fetch(job)

    assert connector.http_client.calls[0][1] == {
        "limit": 100,
        "active": True,
        "closed": False,
    }
    assert batch.next_cursor is None
    assert batch.has_more is False
    assert batch.source_watermark == format_gamma_markets_checkpoint(
        GammaMarketsCheckpoint(
            updated_at=parse_iso_datetime("2026-03-20T00:00:00Z"),
            market_id="gamma-market-1",
        )
    )
    assert batch.records[0].metadata["query_mode"] == "snapshot"


def test_gamma_connector_uses_explicit_backfill_offset_mode() -> None:
    connector = PolymarketGammaMarketsHandler(
        http_client=FakeHttpClient(
            {
                "https://gamma-api.polymarket.com/markets": [
                    {"id": "gamma-market-2", "updatedAt": "2026-03-20T00:00:00Z"},
                ]
            }
        )
    )
    job = IngestionJob(
        job_id="job-2",
        source="polymarket_gamma",
        dataset="markets",
        params={"limit": 1, "offset": 0, "active": True, "closed": False, "mode": "backfill"},
        cursor="offset=100",
    )

    batch = connector.fetch(job)

    assert connector.http_client.calls[0][1] == {
        "limit": 1,
        "active": True,
        "closed": False,
        "offset": 100,
    }
    assert batch.next_cursor == "offset=101"
    assert batch.has_more is True
    assert batch.records[0].metadata["query_mode"] == "backfill"
