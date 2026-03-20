from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from poly_arbitrage.ingestion.runtime import build_api_app
    from poly_arbitrage.ingestion.settings import IngestionSettings

    uvicorn.run(
        build_api_app(IngestionSettings()),
        host="0.0.0.0",
        port=8000,
    )


if __name__ == "__main__":
    main()
