from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from poly_arbitrage.ingestion.runtime import build_runtime
    from poly_arbitrage.ingestion.settings import IngestionSettings

    runtime = build_runtime(IngestionSettings())
    runtime.worker.run_forever()


if __name__ == "__main__":
    main()
