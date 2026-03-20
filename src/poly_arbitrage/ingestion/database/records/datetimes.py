from __future__ import annotations

from datetime import UTC, datetime


def ensure_utc_datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"expected datetime, received {type(value).__name__}")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
