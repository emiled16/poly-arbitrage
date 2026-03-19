from __future__ import annotations


class PolymarketAPIError(RuntimeError):
    """Raised when an upstream Polymarket endpoint cannot be read safely."""
