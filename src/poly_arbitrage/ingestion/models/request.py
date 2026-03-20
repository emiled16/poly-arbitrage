from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from poly_arbitrage.ingestion.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class IngestionRequest:
    source: str
    dataset: str
    params: dict[str, Any] = field(default_factory=dict)
    cursor: str | None = None
    checkpoint_key: str | None = None
    trigger: str = "manual"
    requested_at: datetime = field(default_factory=utc_now)
    idempotency_key: str | None = None
