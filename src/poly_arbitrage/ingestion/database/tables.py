from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)

from poly_arbitrage.ingestion.database.metadata import INGESTION_METADATA

INGESTION_JOBS_TABLE = Table(
    "ingestion_jobs",
    INGESTION_METADATA,
    Column("job_id", String(64), primary_key=True),
    Column("source", String(128), nullable=False),
    Column("dataset", String(128), nullable=False),
    Column("params", JSON, nullable=False),
    Column("cursor", Text, nullable=True),
    Column("checkpoint_key", String(255), nullable=True),
    Column("trigger", String(64), nullable=False),
    Column("requested_at", DateTime(timezone=True), nullable=False),
    Column("available_at", DateTime(timezone=True), nullable=False),
    Column("status", String(32), nullable=False),
    Column("attempts", Integer, nullable=False, default=0),
    Column("worker_id", String(128), nullable=True),
    Column("queued_at", DateTime(timezone=True), nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("last_error", Text, nullable=True),
    Column("idempotency_key", String(255), nullable=True),
    Column("batch_id", String(64), nullable=True),
    Column("object_uri", Text, nullable=True),
    Column("record_count", Integer, nullable=True),
    Column("next_cursor", Text, nullable=True),
    Column("has_more", Boolean, nullable=False, default=False),
    Column("source_watermark", String(255), nullable=True),
    UniqueConstraint(
        "source",
        "dataset",
        "idempotency_key",
        name="uq_ingestion_jobs_source_dataset_idempotency",
    ),
)

Index(
    "ix_ingestion_jobs_status_available_at",
    INGESTION_JOBS_TABLE.c.status,
    INGESTION_JOBS_TABLE.c.available_at,
)
Index(
    "ix_ingestion_jobs_source_dataset_status",
    INGESTION_JOBS_TABLE.c.source,
    INGESTION_JOBS_TABLE.c.dataset,
    INGESTION_JOBS_TABLE.c.status,
)

INGESTION_CURSORS_TABLE = Table(
    "ingestion_cursors",
    INGESTION_METADATA,
    Column("source", String(128), primary_key=True),
    Column("dataset", String(128), primary_key=True),
    Column("checkpoint_key", String(255), primary_key=True),
    Column("cursor", Text, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

INGESTION_SCHEDULES_TABLE = Table(
    "ingestion_schedules",
    INGESTION_METADATA,
    Column("schedule_id", String(64), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("source", String(128), nullable=False),
    Column("dataset", String(128), nullable=False),
    Column("cadence_seconds", Integer, nullable=False),
    Column("params", JSON, nullable=False),
    Column("bootstrap_cursor", Text, nullable=True),
    Column("trigger", String(64), nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("next_run_at", DateTime(timezone=True), nullable=False),
    Column("last_enqueued_at", DateTime(timezone=True), nullable=True),
)

Index("ix_ingestion_schedules_next_run_at", INGESTION_SCHEDULES_TABLE.c.next_run_at)
