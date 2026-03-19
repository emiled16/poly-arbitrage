from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from poly_arbitrage.elt.polymarket.parsers.value_parsers import parse_decimal


def best_price(levels: Any) -> Any:
    if not isinstance(levels, list) or not levels:
        return None
    first_level = levels[0]
    if not isinstance(first_level, Mapping):
        return None
    return parse_decimal(first_level.get("price"))
