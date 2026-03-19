from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def parse_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)

    if isinstance(value, str) and value.isdigit():
        return datetime.fromtimestamp(int(value), tz=UTC)

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    return None


def parse_jsonish_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return [raw]
        if isinstance(decoded, list):
            return decoded
        return [decoded]
    return [value]


def first_mapping(value: Any) -> Mapping[str, Any] | None:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return None

    for item in value:
        if isinstance(item, Mapping):
            return item
    return None
