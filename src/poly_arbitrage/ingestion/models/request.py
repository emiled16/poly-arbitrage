from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class IngestionRequest:
    source: str
    dataset: str
    params: dict[str, Any] = field(default_factory=dict)
    cursor: str | None = None
