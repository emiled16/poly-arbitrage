from __future__ import annotations

from typing import Any


def item_or_none(values: list[Any], index: int) -> Any:
    if index >= len(values):
        return None
    return values[index]


def string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
