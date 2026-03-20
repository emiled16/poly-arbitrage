from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260319_2230"
down_revision = "20260319_2130"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ingestion_jobs",
        sa.Column("checkpoint_key", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "ingestion_cursors_v2",
        sa.Column("source", sa.String(length=128), primary_key=True),
        sa.Column("dataset", sa.String(length=128), primary_key=True),
        sa.Column("checkpoint_key", sa.String(length=255), primary_key=True),
        sa.Column("cursor", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        """
        INSERT INTO ingestion_cursors_v2 (source, dataset, checkpoint_key, cursor, updated_at)
        SELECT source, dataset, 'legacy', cursor, updated_at
        FROM ingestion_cursors
        """
    )
    op.drop_table("ingestion_cursors")
    op.rename_table("ingestion_cursors_v2", "ingestion_cursors")


def downgrade() -> None:
    op.create_table(
        "ingestion_cursors_v1",
        sa.Column("source", sa.String(length=128), primary_key=True),
        sa.Column("dataset", sa.String(length=128), primary_key=True),
        sa.Column("cursor", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        """
        INSERT INTO ingestion_cursors_v1 (source, dataset, cursor, updated_at)
        SELECT source, dataset, cursor, updated_at
        FROM ingestion_cursors
        WHERE checkpoint_key = 'legacy'
        """
    )
    op.drop_table("ingestion_cursors")
    op.rename_table("ingestion_cursors_v1", "ingestion_cursors")
    op.drop_column("ingestion_jobs", "checkpoint_key")
