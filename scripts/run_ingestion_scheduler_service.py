from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from poly_arbitrage.ingestion.runtime import build_runtime
    from poly_arbitrage.ingestion.scheduler_service import PollingSchedulerService
    from poly_arbitrage.ingestion.settings import IngestionSettings

    logging.basicConfig(
        level=os.getenv("POLY_ARB_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    runtime = build_runtime(IngestionSettings())
    service = PollingSchedulerService(
        scheduler=runtime.scheduler,
        interval_seconds=float(os.getenv("POLY_ARB_INGESTION_SCHEDULER_INTERVAL_SECONDS", "30")),
        limit=int(os.getenv("POLY_ARB_INGESTION_SCHEDULER_LIMIT", "100")),
    )
    service.run_forever()


if __name__ == "__main__":
    main()
