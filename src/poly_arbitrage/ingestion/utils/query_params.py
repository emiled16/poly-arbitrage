from __future__ import annotations

from collections.abc import Mapping


def normalize_query_params(
    params: Mapping[str, str | int | bool | None] | None,
) -> dict[str, str]:
    if not params:
        return {}

    normalized: dict[str, str] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            normalized[key] = "true" if value else "false"
            continue
        normalized[key] = str(value)
    return normalized
