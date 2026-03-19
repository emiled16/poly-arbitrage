from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class RawIngestionRecord:
    source: str
    dataset: str
    job_id: str
    endpoint: str
    fetched_at: datetime
    request_params: dict[str, Any]
    payload: Any
    content_hash: str
    cursor: str | None = None
    response_status: int = 200
    metadata: dict[str, Any] = field(default_factory=dict)
