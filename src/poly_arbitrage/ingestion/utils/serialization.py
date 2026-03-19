from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any


def serialize_value(value: Any) -> Any:
    if is_dataclass(value):
        return {key: serialize_value(item) for key, item in asdict(value).items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [serialize_value(item) for item in value]
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_value(item) for key, item in value.items()}
    return value


def stable_json_dumps(value: Any) -> str:
    return json.dumps(
        serialize_value(value),
        sort_keys=True,
        separators=(",", ":"),
    )


def build_content_hash(payload: Any) -> str:
    return sha256(stable_json_dumps(payload).encode("utf-8")).hexdigest()
