from __future__ import annotations

from typing import Any

from poly_arbitrage.ingestion.models.raw_record import RawIngestionRecord
from poly_arbitrage.ingestion.utils.clock import utc_now
from poly_arbitrage.ingestion.utils.serialization import build_content_hash


def build_raw_record(
    *,
    source: str,
    dataset: str,
    job_id: str,
    endpoint: str,
    request_params: dict[str, Any],
    payload: Any,
    cursor: str | None = None,
    response_status: int = 200,
    metadata: dict[str, Any] | None = None,
) -> RawIngestionRecord:
    return RawIngestionRecord(
        source=source,
        dataset=dataset,
        job_id=job_id,
        endpoint=endpoint,
        fetched_at=utc_now(),
        request_params=request_params,
        payload=payload,
        content_hash=build_content_hash(payload),
        cursor=cursor,
        response_status=response_status,
        metadata=metadata or {},
    )
