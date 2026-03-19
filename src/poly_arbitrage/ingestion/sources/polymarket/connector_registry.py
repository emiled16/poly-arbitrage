from __future__ import annotations

from poly_arbitrage.ingestion.protocols.source_connector import SourceConnector
from poly_arbitrage.ingestion.sources.polymarket.connectors.clob_book_connector import (
    PolymarketClobBookConnector,
)
from poly_arbitrage.ingestion.sources.polymarket.connectors.clob_midpoint_connector import (
    PolymarketClobMidpointConnector,
)
from poly_arbitrage.ingestion.sources.polymarket.connectors.gamma_markets_connector import (
    PolymarketGammaMarketsConnector,
)


def build_polymarket_connector_registry() -> dict[tuple[str, str], SourceConnector]:
    connectors: list[SourceConnector] = [
        PolymarketGammaMarketsConnector(),
        PolymarketClobBookConnector(),
        PolymarketClobMidpointConnector(),
    ]
    return {(connector.source_name, connector.dataset_name): connector for connector in connectors}
