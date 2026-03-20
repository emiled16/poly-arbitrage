from __future__ import annotations

from enum import StrEnum


class IngestionJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    RETRY_PENDING = "retry_pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"
