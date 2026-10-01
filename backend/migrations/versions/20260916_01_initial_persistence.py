"""Create complete intake persistence schema."""

from alembic import op
import sqlalchemy as sa

revision = "20260916_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keeping the migration sourced from metadata prevents the hand-written
    # migration from drifting away from the tested ORM schema.
    from models import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    for table_name in (
        "doctor_reviews", "audit_events", "intake_reports", "recommended_exams",
        "follow_up_answers", "intake_field_states", "baseline_measurements",
        "intake_sessions", "patients",
    ):
        op.drop_table(table_name)
