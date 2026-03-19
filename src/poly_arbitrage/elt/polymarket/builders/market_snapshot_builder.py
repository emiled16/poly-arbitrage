from __future__ import annotations

from poly_arbitrage.elt.polymarket.models.market import PolymarketMarket
from poly_arbitrage.elt.polymarket.models.market_price_snapshot import MarketPriceSnapshot
from poly_arbitrage.elt.polymarket.models.token_order_book_snapshot import (
    TokenOrderBookSnapshot,
)


def build_market_snapshot(
    *,
    market: PolymarketMarket,
    yes_snapshot: TokenOrderBookSnapshot,
    no_snapshot: TokenOrderBookSnapshot,
) -> MarketPriceSnapshot:
    observed_at = max(yes_snapshot.observed_at, no_snapshot.observed_at)
    yes_probability = market.yes_contract.implied_probability if market.yes_contract else None
    no_probability = market.no_contract.implied_probability if market.no_contract else None
    yes_price = yes_snapshot.midpoint or yes_snapshot.last_trade_price or yes_probability
    no_price = no_snapshot.midpoint or no_snapshot.last_trade_price or no_probability

    return MarketPriceSnapshot(
        condition_id=market.condition_id,
        observed_at=observed_at,
        yes_token_id=yes_snapshot.token_id,
        no_token_id=no_snapshot.token_id,
        yes_price=yes_price,
        no_price=no_price,
        yes_bid=yes_snapshot.best_bid,
        yes_ask=yes_snapshot.best_ask,
        no_bid=no_snapshot.best_bid,
        no_ask=no_snapshot.best_ask,
        spread=yes_snapshot.spread,
        market_prob_baseline=yes_price,
        liquidity=market.liquidity,
        volume_24h=market.volume_24h,
    )
