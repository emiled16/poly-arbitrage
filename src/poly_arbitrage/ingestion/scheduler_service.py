from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from poly_arbitrage.ingestion.scheduler import IngestionScheduler

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PollingSchedulerService:
    scheduler: IngestionScheduler
    interval_seconds: float = 30.0
    limit: int = 100
    sleep: Callable[[float], None] = field(default=time.sleep, repr=False)

    def run_once(self) -> dict[str, list[str]]:
        result = self.scheduler.enqueue_due_work(limit=self.limit)
        LOGGER.info(
            "enqueued due ingestion work",
            extra=build_scheduler_log_context(result=result, limit=self.limit),
        )
        return result

    def run_forever(self) -> None:
        while True:
            self.run_once()
            self.sleep(self.interval_seconds)


def build_scheduler_log_context(
    *,
    result: dict[str, list[str]],
    limit: int,
) -> dict[str, Any]:
    scheduled_job_ids = result.get("scheduled_job_ids", [])
    retry_job_ids = result.get("retry_job_ids", [])
    return {
        "limit": limit,
        "scheduled_count": len(scheduled_job_ids),
        "retry_count": len(retry_job_ids),
    }
