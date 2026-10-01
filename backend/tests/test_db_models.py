import unittest

from sqlalchemy import create_engine, inspect
from sqlalchemy import text


class DatabaseModelTests(unittest.TestCase):
    def test_all_persistence_tables_are_created(self):
        from models import Base

        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)

        self.assertEqual(
            set(inspect(engine).get_table_names()),
            {
                "patients",
                "intake_sessions",
                "baseline_measurements",
                "intake_field_states",
                "follow_up_answers",
                "recommended_exams",
                "intake_reports",
                "audit_events",
                "doctor_reviews",
            },
        )
        engine.dispose()

    def test_database_revision_must_match_application_head(self):
        from db import check_database_revision

        engine = create_engine("sqlite+pysqlite:///:memory:")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES ('20260917_03')")
            )

        self.assertTrue(check_database_revision(engine))
        engine.dispose()

    def test_intake_sessions_support_soft_archiving(self):
        from models import Base

        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)

        columns = {column["name"]: column for column in inspect(engine).get_columns("intake_sessions")}
        self.assertIn("archived_at", columns)
        self.assertTrue(columns["archived_at"]["nullable"])
        engine.dispose()

    def test_intake_reports_support_soft_deletion(self):
        from models import Base

        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)

        columns = {
            column["name"]: column
            for column in inspect(engine).get_columns("intake_reports")
        }
        self.assertIn("deleted_at", columns)
        self.assertTrue(columns["deleted_at"]["nullable"])
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
