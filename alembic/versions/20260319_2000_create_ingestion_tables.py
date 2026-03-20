from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260319_2000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_jobs",
        sa.Column("job_id", sa.String(length=64), primary_key=True),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("dataset", sa.String(length=128), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("cursor", sa.Text(), nullable=True),
        sa.Column("trigger", sa.String(length=64), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("batch_id", sa.String(length=64), nullable=True),
        sa.Column("object_uri", sa.Text(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=True),
        sa.Column("next_cursor", sa.Text(), nullable=True),
        sa.Column("has_more", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_watermark", sa.String(length=255), nullable=True),
        sa.UniqueConstraint(
            "source",
            "dataset",
            "idempotency_key",
            name="uq_ingestion_jobs_source_dataset_idempotency",
        ),
    )
    op.create_index(
        "ix_ingestion_jobs_status_available_at",
        "ingestion_jobs",
        ["status", "available_at"],
    )
    op.create_index(
        "ix_ingestion_jobs_source_dataset_status",
        "ingestion_jobs",
        ["source", "dataset", "status"],
    )

    op.create_table(
        "ingestion_cursors",
        sa.Column("source", sa.String(length=128), primary_key=True),
        sa.Column("dataset", sa.String(length=128), primary_key=True),
        sa.Column("cursor", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "ingestion_schedules",
        sa.Column("schedule_id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("dataset", sa.String(length=128), nullable=False),
        sa.Column("cadence_seconds", sa.Integer(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("cursor", sa.Text(), nullable=True),
        sa.Column("trigger", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_enqueued_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_ingestion_schedules_next_run_at",
        "ingestion_schedules",
        ["next_run_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_schedules_next_run_at", table_name="ingestion_schedules")
    op.drop_table("ingestion_schedules")
    op.drop_table("ingestion_cursors")
    op.drop_index("ix_ingestion_jobs_source_dataset_status", table_name="ingestion_jobs")
    op.drop_index("ix_ingestion_jobs_status_available_at", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
