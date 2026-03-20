from __future__ import annotations

import pytest

from poly_arbitrage.ingestion.scheduler_service import (
    PollingSchedulerService,
    build_scheduler_log_context,
)


class FakeScheduler:
    def __init__(self) -> None:
        self.limits: list[int] = []

    def enqueue_due_work(self, *, limit: int = 100) -> dict[str, list[str]]:
        self.limits.append(limit)
        return {
            "scheduled_job_ids": ["job-1", "job-2"],
            "retry_job_ids": ["job-3"],
        }


def test_polling_scheduler_service_runs_once() -> None:
    scheduler = FakeScheduler()
    service = PollingSchedulerService(scheduler=scheduler, interval_seconds=5.0, limit=25)

    result = service.run_once()

    assert scheduler.limits == [25]
    assert result == {
        "scheduled_job_ids": ["job-1", "job-2"],
        "retry_job_ids": ["job-3"],
    }


def test_polling_scheduler_service_runs_forever_until_interrupted() -> None:
    scheduler = FakeScheduler()
    sleep_calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        raise KeyboardInterrupt

    service = PollingSchedulerService(
        scheduler=scheduler,
        interval_seconds=15.0,
        limit=10,
        sleep=fake_sleep,
    )

    with pytest.raises(KeyboardInterrupt):
        service.run_forever()

    assert scheduler.limits == [10]
    assert sleep_calls == [15.0]


def test_build_scheduler_log_context_counts_jobs() -> None:
    context = build_scheduler_log_context(
        result={
            "scheduled_job_ids": ["job-1"],
            "retry_job_ids": ["job-2", "job-3"],
        },
        limit=50,
    )

    assert context == {
        "limit": 50,
        "scheduled_count": 1,
        "retry_count": 2,
    }
