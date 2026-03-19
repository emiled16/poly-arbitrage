from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from poly_arbitrage.elt.polymarket.models.market import PolymarketMarket
from poly_arbitrage.elt.polymarket.models.outcome_contract import OutcomeContract
from poly_arbitrage.elt.polymarket.parsers.payload_helpers import item_or_none, string_or_none
from poly_arbitrage.elt.polymarket.parsers.value_parsers import (
    first_mapping,
    parse_datetime,
    parse_decimal,
    parse_jsonish_list,
)
from poly_arbitrage.ingestion.models.raw_record import RawIngestionRecord


def normalize_gamma_record(record: RawIngestionRecord) -> list[PolymarketMarket]:
    return normalize_gamma_payload(record.payload)


def normalize_gamma_payload(payload: Any) -> list[PolymarketMarket]:
    if not isinstance(payload, list):
        raise TypeError("Gamma raw payload must be a list")

    return [normalize_gamma_market(item) for item in payload if isinstance(item, Mapping)]


def normalize_gamma_market(payload: Mapping[str, Any]) -> PolymarketMarket:
    event = first_mapping(payload.get("events"))
    outcomes = parse_jsonish_list(payload.get("outcomes"))
    prices = parse_jsonish_list(payload.get("outcomePrices"))
    token_ids = parse_jsonish_list(payload.get("clobTokenIds"))

    normalized_outcomes: list[OutcomeContract] = []
    for index, outcome in enumerate(outcomes):
        normalized_outcomes.append(
            OutcomeContract(
                label=str(outcome),
                token_id=item_or_none(token_ids, index),
                implied_probability=parse_decimal(item_or_none(prices, index)),
            )
        )

    return PolymarketMarket(
        gamma_market_id=str(payload.get("id", "")),
        condition_id=str(payload.get("conditionId") or payload.get("questionID") or payload.get("id", "")),
        question=str(payload.get("question", "")),
        slug=string_or_none(payload.get("slug")),
        description=string_or_none(payload.get("description")),
        resolution_source=string_or_none(payload.get("resolutionSource")),
        category=string_or_none(payload.get("category"))
        or string_or_none(event.get("category") if event else None),
        market_type=string_or_none(payload.get("marketType")),
        start_time=parse_datetime(payload.get("startDateIso") or payload.get("startDate")),
        end_time=parse_datetime(payload.get("endDateIso") or payload.get("endDate")),
        close_time=parse_datetime(payload.get("closedTime")),
        active=bool(payload.get("active")),
        closed=bool(payload.get("closed")),
        archived=bool(payload.get("archived")),
        accepting_orders=bool(payload.get("acceptingOrders")),
        liquidity=parse_decimal(payload.get("liquidityNum") or payload.get("liquidity")),
        volume=parse_decimal(payload.get("volumeNum") or payload.get("volume")),
        volume_24h=parse_decimal(payload.get("volume24hr")),
        event_id=string_or_none(event.get("id") if event else None),
        event_title=string_or_none(event.get("title") if event else None),
        outcomes=tuple(normalized_outcomes),
    )
