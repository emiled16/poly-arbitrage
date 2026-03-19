from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from poly_arbitrage.elt.polymarket.models.outcome_contract import OutcomeContract


@dataclass(frozen=True, slots=True)
class PolymarketMarket:
    gamma_market_id: str
    condition_id: str
    question: str
    slug: str | None
    description: str | None
    resolution_source: str | None
    category: str | None
    market_type: str | None
    start_time: datetime | None
    end_time: datetime | None
    close_time: datetime | None
    active: bool
    closed: bool
    archived: bool
    accepting_orders: bool
    liquidity: Decimal | None
    volume: Decimal | None
    volume_24h: Decimal | None
    event_id: str | None
    event_title: str | None
    outcomes: tuple[OutcomeContract, ...]

    def outcome_by_label(self, label: str) -> OutcomeContract | None:
        normalized = label.strip().casefold()
        for outcome in self.outcomes:
            if outcome.normalized_label == normalized:
                return outcome
        return None

    @property
    def yes_contract(self) -> OutcomeContract | None:
        return self.outcome_by_label("yes")

    @property
    def no_contract(self) -> OutcomeContract | None:
        return self.outcome_by_label("no")
