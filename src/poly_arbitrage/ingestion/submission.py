from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.models.schedule import IngestionSchedule

GAMMA_MARKETS_SNAPSHOT_MODE = "snapshot"
GAMMA_MARKETS_BACKFILL_MODE = "backfill"


def normalize_request(request: IngestionRequest) -> IngestionRequest:
    normalized_params = normalize_params(
        source=request.source,
        dataset=request.dataset,
        params=request.params,
        cursor=request.cursor,
        is_schedule=request.trigger == "schedule",
    )
    return replace(request, params=normalized_params)


def validate_schedule(schedule: IngestionSchedule) -> IngestionSchedule:
    normalized_params = normalize_params(
        source=schedule.source,
        dataset=schedule.dataset,
        params=schedule.params,
        cursor=schedule.bootstrap_cursor,
        is_schedule=True,
    )
    return replace(schedule, params=normalized_params)


def build_schedule_checkpoint_key(schedule: IngestionSchedule) -> str:
    return f"schedule:{schedule.schedule_id}"


def build_schedule_job_idempotency_key(
    schedule: IngestionSchedule,
    *,
    due_at: datetime,
) -> str:
    due_token = due_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return f"schedule:{schedule.schedule_id}:{due_token}"


def normalize_params(
    *,
    source: str,
    dataset: str,
    params: dict[str, Any],
    cursor: str | None,
    is_schedule: bool,
) -> dict[str, Any]:
    normalized = dict(params)
    if source == "polymarket_gamma" and dataset == "markets":
        return normalize_gamma_markets_params(
            params=normalized,
            cursor=cursor,
            is_schedule=is_schedule,
        )
    if source == "polymarket_clob":
        token_id = normalized.get("token_id")
        if not isinstance(token_id, str) or not token_id:
            raise ValueError("CLOB ingestion submissions require a non-empty token_id")
    return normalized


def normalize_gamma_markets_params(
    *,
    params: dict[str, Any],
    cursor: str | None,
    is_schedule: bool,
) -> dict[str, Any]:
    mode = params.get("mode", GAMMA_MARKETS_SNAPSHOT_MODE)
    if not isinstance(mode, str):
        raise ValueError("Gamma markets mode must be a string")
    if mode not in {GAMMA_MARKETS_SNAPSHOT_MODE, GAMMA_MARKETS_BACKFILL_MODE}:
        raise ValueError("Gamma markets mode must be 'snapshot' or 'backfill'")

    normalized = dict(params)
    normalized["mode"] = mode

    limit = normalized.get("limit")
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("Gamma markets limit must be a positive integer")

    if mode == GAMMA_MARKETS_SNAPSHOT_MODE:
        if "offset" in normalized:
            raise ValueError("Gamma snapshot ingestion cannot include offset")
        if cursor is not None:
            raise ValueError("Gamma snapshot ingestion cannot include a cursor")
        return normalized

    if is_schedule:
        raise ValueError("Recurring Gamma schedules must use snapshot mode")

    offset = normalized.get("offset", 0)
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("Gamma backfill offset must be a non-negative integer")
    normalized["offset"] = offset
    return normalized
