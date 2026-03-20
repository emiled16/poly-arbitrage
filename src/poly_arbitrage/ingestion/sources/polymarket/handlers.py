from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs

from poly_arbitrage.ingestion.contracts import SourceHandler
from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.raw_record import build_raw_record
from poly_arbitrage.ingestion.sources.polymarket.client import PolymarketJsonHttpClient
from poly_arbitrage.ingestion.submission import (
    GAMMA_MARKETS_BACKFILL_MODE,
    GAMMA_MARKETS_SNAPSHOT_MODE,
)


def build_polymarket_handlers() -> list[SourceHandler]:
    return [
        PolymarketGammaMarketsHandler(),
        PolymarketClobBookHandler(),
        PolymarketClobMidpointHandler(),
    ]


@dataclass(slots=True)
class PolymarketGammaMarketsHandler:
    http_client: Any = field(default_factory=PolymarketJsonHttpClient)
    base_url: str = "https://gamma-api.polymarket.com"
    source_name: str = "polymarket_gamma"
    dataset_name: str = "markets"

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        endpoint = f"{self.base_url}/markets"
        effective_params = resolve_gamma_markets_request_params(job)
        payload = self.http_client.get_json(endpoint, params=effective_params)
        mode = gamma_markets_mode(job)

        record = build_raw_record(
            source=self.source_name,
            dataset=self.dataset_name,
            job_id=job.job_id,
            endpoint=endpoint,
            request_params=effective_params,
            payload=payload,
            cursor=job.cursor,
            metadata={
                "response_shape": response_shape(payload),
                "item_count": len(payload) if isinstance(payload, list) else None,
                "response_item_count": len(payload) if isinstance(payload, list) else None,
                "query_mode": mode,
                "rows_kept_after_filtering": len(payload) if isinstance(payload, list) else None,
                "rows_dropped_as_already_seen": 0,
                "page_count": 1,
            },
        )

        next_cursor = (
            next_offset_cursor(effective_params, payload)
            if mode == GAMMA_MARKETS_BACKFILL_MODE
            else None
        )

        return IngestionBatch(
            source=self.source_name,
            dataset=self.dataset_name,
            job_id=job.job_id,
            records=[record],
            next_cursor=next_cursor,
            has_more=next_cursor is not None,
            source_watermark=gamma_markets_source_watermark(payload),
        )


@dataclass(slots=True)
class PolymarketClobBookHandler:
    http_client: Any = field(default_factory=PolymarketJsonHttpClient)
    base_url: str = "https://clob.polymarket.com"
    source_name: str = "polymarket_clob"
    dataset_name: str = "book"

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        return build_clob_batch(
            http_client=self.http_client,
            base_url=self.base_url,
            source_name=self.source_name,
            dataset_name=self.dataset_name,
            job=job,
        )


@dataclass(slots=True)
class PolymarketClobMidpointHandler:
    http_client: Any = field(default_factory=PolymarketJsonHttpClient)
    base_url: str = "https://clob.polymarket.com"
    source_name: str = "polymarket_clob"
    dataset_name: str = "midpoint"

    def fetch(self, job: IngestionJob) -> IngestionBatch:
        return build_clob_batch(
            http_client=self.http_client,
            base_url=self.base_url,
            source_name=self.source_name,
            dataset_name=self.dataset_name,
            job=job,
        )


def build_clob_batch(
    *,
    http_client: Any,
    base_url: str,
    source_name: str,
    dataset_name: str,
    job: IngestionJob,
) -> IngestionBatch:
    token_id = job.params.get("token_id")
    if not isinstance(token_id, str) or not token_id:
        raise ValueError("CLOB ingestion jobs require a non-empty token_id")

    endpoint = f"{base_url}/{dataset_name}"
    payload = http_client.get_json(endpoint, params={"token_id": token_id})

    record = build_raw_record(
        source=source_name,
        dataset=dataset_name,
        job_id=job.job_id,
        endpoint=endpoint,
        request_params={"token_id": token_id},
        payload=payload,
        cursor=job.cursor,
        metadata={
            "response_shape": response_shape(payload),
            "token_id": token_id,
            "query_mode": "snapshot",
            "page_count": 1,
        },
    )

    return IngestionBatch(
        source=source_name,
        dataset=dataset_name,
        job_id=job.job_id,
        records=[record],
    )


def response_shape(payload: object) -> str:
    if isinstance(payload, list):
        return "list"
    if isinstance(payload, Mapping):
        return "object"
    return type(payload).__name__


def resolve_gamma_markets_request_params(job: IngestionJob) -> dict[str, object]:
    params = {
        key: value for key, value in dict(job.params).items() if key not in {"mode", "offset"}
    }
    if gamma_markets_mode(job) == GAMMA_MARKETS_BACKFILL_MODE:
        params["offset"] = resolve_backfill_offset(job)
    return params


def gamma_markets_mode(job: IngestionJob) -> str:
    mode = job.params.get("mode", GAMMA_MARKETS_SNAPSHOT_MODE)
    if not isinstance(mode, str):
        raise ValueError("Gamma markets mode must be a string")
    if mode not in {GAMMA_MARKETS_SNAPSHOT_MODE, GAMMA_MARKETS_BACKFILL_MODE}:
        raise ValueError("Gamma markets mode must be 'snapshot' or 'backfill'")
    return mode


def resolve_backfill_offset(job: IngestionJob) -> int:
    parsed_cursor = parse_offset_cursor(job.cursor)
    if parsed_cursor is not None:
        return parsed_cursor
    offset = job.params.get("offset", 0)
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("Gamma backfill offset must be a non-negative integer")
    return offset


def parse_offset_cursor(cursor: str | None) -> int | None:
    if not cursor:
        return None
    values = {
        key: parts[-1]
        for key, parts in parse_qs(cursor, keep_blank_values=False).items()
        if parts
    }
    value = values.get("offset")
    if value is None:
        return None
    try:
        offset = int(value)
    except ValueError:
        return None
    if offset < 0:
        return None
    return offset


def next_offset_cursor(params: dict[str, object], payload: object) -> str | None:
    if not isinstance(payload, list):
        return None

    limit = params.get("limit")
    if not isinstance(limit, int) or limit <= 0 or len(payload) < limit:
        return None

    offset = params.get("offset", 0)
    if not isinstance(offset, int):
        return None

    return f"offset={offset + len(payload)}"


def gamma_markets_source_watermark(payload: object) -> str | None:
    checkpoint = first_gamma_markets_checkpoint(payload)
    if checkpoint is None:
        return None
    return format_gamma_markets_checkpoint(checkpoint)


@dataclass(frozen=True, slots=True)
class GammaMarketsCheckpoint:
    updated_at: datetime
    market_id: str


def first_gamma_markets_checkpoint(payload: object) -> GammaMarketsCheckpoint | None:
    if not isinstance(payload, list):
        return None
    for item in payload:
        checkpoint = extract_gamma_markets_checkpoint(item)
        if checkpoint is not None:
            return checkpoint
    return None


def extract_gamma_markets_checkpoint(payload: object) -> GammaMarketsCheckpoint | None:
    if not isinstance(payload, Mapping):
        return None
    updated_at = payload.get("updatedAt")
    market_id = payload.get("id")
    if not isinstance(updated_at, str) or not isinstance(market_id, str):
        return None
    return GammaMarketsCheckpoint(
        updated_at=parse_iso_datetime(updated_at),
        market_id=market_id,
    )


def parse_iso_datetime(value: str) -> datetime:
    normalized_value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized_value).astimezone(UTC)


def format_iso_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def format_gamma_markets_checkpoint(value: GammaMarketsCheckpoint) -> str:
    return (
        f"updated_at={format_iso_datetime(value.updated_at)}"
        f"&id={value.market_id}"
    )
