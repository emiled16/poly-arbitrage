from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OutcomeContract:
    label: str
    token_id: str | None
    implied_probability: Decimal | None

    @property
    def normalized_label(self) -> str:
        return self.label.strip().casefold()
