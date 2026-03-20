from __future__ import annotations

from dataclasses import dataclass

from poly_arbitrage.ingestion.contracts import SourceHandler


@dataclass(slots=True)
class SourceRegistry:
    handlers: dict[tuple[str, str], SourceHandler]

    def get(self, source: str, dataset: str) -> SourceHandler:
        key = (source, dataset)
        handler = self.handlers.get(key)
        if handler is None:
            raise KeyError(f"no handler registered for source={source!r}, dataset={dataset!r}")
        return handler


def build_registry(handlers: list[SourceHandler]) -> SourceRegistry:
    return SourceRegistry(
        handlers={(handler.source_name, handler.dataset_name): handler for handler in handlers},
    )
