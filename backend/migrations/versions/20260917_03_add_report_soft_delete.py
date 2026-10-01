"""Add soft deletion to completed intake reports."""

from alembic import op
import sqlalchemy as sa


revision = "20260917_03"
down_revision = "20260916_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("intake_reports", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index(
        "ix_intake_reports_deleted_at",
        "intake_reports",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_intake_reports_patient_deleted_created",
        "intake_reports",
        ["patient_id", "deleted_at", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_intake_reports_patient_deleted_created", table_name="intake_reports")
    op.drop_index("ix_intake_reports_deleted_at", table_name="intake_reports")
    op.drop_column("intake_reports", "deleted_at")
