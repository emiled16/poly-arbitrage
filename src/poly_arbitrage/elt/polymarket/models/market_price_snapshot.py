from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MarketPriceSnapshot:
    condition_id: str
    observed_at: datetime
    yes_token_id: str | None
    no_token_id: str | None
    yes_price: Decimal | None
    no_price: Decimal | None
    yes_bid: Decimal | None
    yes_ask: Decimal | None
    no_bid: Decimal | None
    no_ask: Decimal | None
    spread: Decimal | None
    market_prob_baseline: Decimal | None
    liquidity: Decimal | None
    volume_24h: Decimal | None
