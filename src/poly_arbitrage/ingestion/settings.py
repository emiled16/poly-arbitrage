from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PostgresSettings:
    dsn: str = os.getenv("POLY_ARB_POSTGRES_DSN", "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/poly_arbitrage")


@dataclass(frozen=True, slots=True)
class RabbitMqSettings:
    url: str = os.getenv("POLY_ARB_RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/%2F")
    queue_name: str = os.getenv("POLY_ARB_RABBITMQ_QUEUE", "ingestion.jobs")
    dead_letter_exchange: str = os.getenv(
        "POLY_ARB_RABBITMQ_DEAD_LETTER_EXCHANGE",
        "ingestion.dead_letter",
    )
    dead_letter_queue_name: str = os.getenv(
        "POLY_ARB_RABBITMQ_DEAD_LETTER_QUEUE",
        "ingestion.jobs.dead_letter",
    )


@dataclass(frozen=True, slots=True)
class RetrySettings:
    max_attempts: int = int(os.getenv("POLY_ARB_INGESTION_MAX_ATTEMPTS", "3"))
    base_delay_seconds: int = int(os.getenv("POLY_ARB_INGESTION_RETRY_BASE_DELAY", "30"))
    max_delay_seconds: int = int(os.getenv("POLY_ARB_INGESTION_RETRY_MAX_DELAY", "300"))

    def delay_seconds_for_attempt(self, attempt_number: int) -> int:
        delay_seconds = self.base_delay_seconds * (2 ** max(attempt_number - 1, 0))
        return min(delay_seconds, self.max_delay_seconds)


@dataclass(frozen=True, slots=True)
class RawStorageSettings:
    backend: str = os.getenv("POLY_ARB_RAW_STORE_BACKEND", "local")
    container_name: str = os.getenv("POLY_ARB_RAW_STORE_CONTAINER", "raw")
    local_root: Path = Path(os.getenv("POLY_ARB_RAW_STORE_ROOT", "artifacts/datasets"))
    s3_endpoint: str = os.getenv("POLY_ARB_MINIO_ENDPOINT", "http://127.0.0.1:9000")
    s3_access_key: str | None = os.getenv("POLY_ARB_MINIO_ACCESS_KEY")
    s3_secret_key: str | None = os.getenv("POLY_ARB_MINIO_SECRET_KEY")
    s3_region: str = os.getenv("POLY_ARB_MINIO_REGION", "us-east-1")
    s3_session_token: str | None = os.getenv("POLY_ARB_MINIO_SESSION_TOKEN")


@dataclass(frozen=True, slots=True)
class IngestionSettings:
    postgres: PostgresSettings = field(default_factory=PostgresSettings)
    rabbitmq: RabbitMqSettings = field(default_factory=RabbitMqSettings)
    retry: RetrySettings = field(default_factory=RetrySettings)
    raw_storage: RawStorageSettings = field(default_factory=RawStorageSettings)
    worker_id: str = os.getenv("POLY_ARB_INGESTION_WORKER_ID", "ingestion-worker-1")
