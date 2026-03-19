from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from poly_arbitrage.ingestion.sources.polymarket.errors import PolymarketAPIError
from poly_arbitrage.ingestion.utils.query_params import normalize_query_params


@dataclass(slots=True)
class UrllibJsonHttpClient:
    timeout_seconds: float = 30.0
    user_agent: str = "poly-arbitrage/0.1.0"

    def get_json(
        self,
        url: str,
        params: Mapping[str, str | int | bool | None] | None = None,
    ) -> Any:
        query = normalize_query_params(params)
        request_url = f"{url}?{urlencode(query)}" if query else url
        request = Request(
            request_url,
            headers={
                "Accept": "application/json",
                "User-Agent": self.user_agent,
            },
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise PolymarketAPIError(
                f"request failed with status {exc.code} for {request_url}: {message}"
            ) from exc
        except URLError as exc:
            raise PolymarketAPIError(f"request failed for {request_url}: {exc.reason}") from exc

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise PolymarketAPIError(f"invalid JSON received from {request_url}") from exc
