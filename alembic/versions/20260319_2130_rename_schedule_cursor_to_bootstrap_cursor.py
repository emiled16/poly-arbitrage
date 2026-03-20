from __future__ import annotations

from alembic import op

revision = "20260319_2130"
down_revision = "20260319_2000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "ingestion_schedules",
        "cursor",
        new_column_name="bootstrap_cursor",
    )


def downgrade() -> None:
    op.alter_column(
        "ingestion_schedules",
        "bootstrap_cursor",
        new_column_name="cursor",
    )
