from __future__ import annotations

from collections.abc import Mapping


def response_shape(payload: object) -> str:
    if isinstance(payload, list):
        return "list"
    if isinstance(payload, Mapping):
        return "object"
    return type(payload).__name__


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
