"""Add soft archiving to intake sessions."""

from alembic import op
import sqlalchemy as sa


revision = "20260916_02"
down_revision = "20260916_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("intake_sessions", sa.Column("archived_at", sa.DateTime(), nullable=True))
    op.create_index(
        "ix_intake_sessions_archived_at",
        "intake_sessions",
        ["archived_at"],
        unique=False,
    )
    op.create_index(
        "ix_intake_sessions_patient_archived_updated",
        "intake_sessions",
        ["patient_id", "archived_at", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_intake_sessions_patient_archived_updated", table_name="intake_sessions")
    op.drop_index("ix_intake_sessions_archived_at", table_name="intake_sessions")
    op.drop_column("intake_sessions", "archived_at")
