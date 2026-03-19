from __future__ import annotations

from dataclasses import dataclass

from poly_arbitrage.elt.polymarket.models.market import PolymarketMarket
from poly_arbitrage.elt.polymarket.models.market_price_snapshot import MarketPriceSnapshot


@dataclass(frozen=True, slots=True)
class IngestedMarketBundle:
    market: PolymarketMarket
    snapshot: MarketPriceSnapshot | None
