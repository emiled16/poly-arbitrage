from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class JsonHttpClient(Protocol):
    def get_json(
        self,
        url: str,
        params: Mapping[str, str | int | bool | None] | None = None,
    ) -> Any:
        """Fetch and decode a JSON response."""
