from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TokenOrderBookSnapshot:
    token_id: str
    market_condition_id: str | None
    observed_at: datetime
    best_bid: Decimal | None
    best_ask: Decimal | None
    midpoint: Decimal | None
    last_trade_price: Decimal | None
    min_order_size: Decimal | None
    tick_size: Decimal | None

    @property
    def spread(self) -> Decimal | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid
