from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from poly_arbitrage.elt.polymarket.builders.market_snapshot_builder import (
    build_market_snapshot,
)
from poly_arbitrage.elt.polymarket.models.market_price_snapshot import (
    MarketPriceSnapshot,
)
from poly_arbitrage.elt.polymarket.normalizers.clob_snapshot_normalizer import (
    normalize_clob_payloads,
)
from poly_arbitrage.elt.polymarket.normalizers.gamma_market_normalizer import (
    normalize_gamma_payload,
)


def test_normalize_gamma_payload_maps_binary_market_fields() -> None:
    markets = normalize_gamma_payload(
        [
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
                "events": [
                    {
                        "id": "event-1",
                        "title": "Election Event",
                        "category": "Politics",
                    }
                ],
            }
        ]
    )

    assert len(markets) == 1
    market = markets[0]
    assert market.condition_id == "condition-1"
    assert market.event_id == "event-1"
    assert market.yes_contract.token_id == "yes-token"
    assert market.no_contract.token_id == "no-token"
    assert market.yes_contract.implied_probability == Decimal("0.61")
    assert market.no_contract.implied_probability == Decimal("0.39")
    assert market.liquidity == Decimal("1212.5")
    assert market.volume_24h == Decimal("120.5")


def test_build_market_snapshot_from_normalized_clob_payloads() -> None:
    market = normalize_gamma_payload(
        [
            {
                "id": "gamma-market-1",
                "conditionId": "condition-1",
                "question": "Will candidate X win?",
                "active": True,
                "closed": False,
                "archived": False,
                "acceptingOrders": True,
                "liquidityNum": 4000,
                "volumeNum": 10000,
                "volume24hr": 250,
                "outcomes": "[\"Yes\", \"No\"]",
                "outcomePrices": "[\"0.49\", \"0.51\"]",
                "clobTokenIds": "[\"yes-token\", \"no-token\"]",
            }
        ]
    )[0]
    yes_snapshot = normalize_clob_payloads(
        book_payload={
            "market": "condition-1",
            "asset_id": "yes-token",
            "timestamp": "1773835200",
            "bids": [{"price": "0.50", "size": "100"}],
            "asks": [{"price": "0.54", "size": "110"}],
            "min_order_size": "1",
            "tick_size": "0.01",
            "last_trade_price": "0.51",
        },
        midpoint_payload={"mid_price": "0.52"},
        token_id="yes-token",
    )
    no_snapshot = normalize_clob_payloads(
        book_payload={
            "market": "condition-1",
            "asset_id": "no-token",
            "timestamp": "1773835260",
            "bids": [{"price": "0.46", "size": "100"}],
            "asks": [{"price": "0.50", "size": "110"}],
            "min_order_size": "1",
            "tick_size": "0.01",
            "last_trade_price": "0.49",
        },
        midpoint_payload={"mid_price": "0.48"},
        token_id="no-token",
    )

    snapshot = build_market_snapshot(
        market=market,
        yes_snapshot=yes_snapshot,
        no_snapshot=no_snapshot,
    )

    assert isinstance(snapshot, MarketPriceSnapshot)
    assert snapshot.condition_id == "condition-1"
    assert snapshot.observed_at == datetime.fromtimestamp(1773835260, tz=UTC)
    assert snapshot.yes_price == Decimal("0.52")
    assert snapshot.no_price == Decimal("0.48")
    assert snapshot.market_prob_baseline == Decimal("0.52")
    assert snapshot.spread == Decimal("0.04")
