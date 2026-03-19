from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from poly_arbitrage.elt.polymarket.models.token_order_book_snapshot import (
    TokenOrderBookSnapshot,
)
from poly_arbitrage.elt.polymarket.parsers.order_book_levels import best_price
from poly_arbitrage.elt.polymarket.parsers.payload_helpers import string_or_none
from poly_arbitrage.elt.polymarket.parsers.value_parsers import parse_datetime, parse_decimal
from poly_arbitrage.ingestion.models.raw_record import RawIngestionRecord


def normalize_clob_records(
    *,
    book_record: RawIngestionRecord,
    midpoint_record: RawIngestionRecord,
) -> TokenOrderBookSnapshot:
    if not isinstance(book_record.payload, Mapping):
        raise TypeError("CLOB book payload must be an object")
    if not isinstance(midpoint_record.payload, Mapping):
        raise TypeError("CLOB midpoint payload must be an object")

    return normalize_clob_payloads(
        book_payload=book_record.payload,
        midpoint_payload=midpoint_record.payload,
        token_id=book_record.request_params.get("token_id"),
    )


def normalize_clob_payloads(
    *,
    book_payload: Mapping[str, Any],
    midpoint_payload: Mapping[str, Any],
    token_id: str | None = None,
) -> TokenOrderBookSnapshot:
    bids = book_payload.get("bids")
    asks = book_payload.get("asks")
    midpoint = parse_decimal(
        midpoint_payload.get("mid")
        or midpoint_payload.get("mid_price")
        or midpoint_payload.get("midpoint")
    )

    return TokenOrderBookSnapshot(
        token_id=str(book_payload.get("asset_id") or token_id or ""),
        market_condition_id=string_or_none(book_payload.get("market")),
        observed_at=parse_datetime(book_payload.get("timestamp")) or datetime.fromtimestamp(0, tz=UTC),
        best_bid=best_price(bids),
        best_ask=best_price(asks),
        midpoint=midpoint,
        last_trade_price=parse_decimal(book_payload.get("last_trade_price")),
        min_order_size=parse_decimal(book_payload.get("min_order_size")),
        tick_size=parse_decimal(book_payload.get("tick_size")),
    )
