import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base
from models import FollowUpAnswer


class PatientOwnershipMigrationTests(unittest.TestCase):
    def setUp(self):
        from repository import SqlAlchemyIntakeRepository

        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.repository = SqlAlchemyIntakeRepository(self.session_factory)

    def tearDown(self):
        self.engine.dispose()

    def test_name_mapping(self):
        from scripts.migrate_patient_ownership import patient_id_for_name

        self.assertEqual(patient_id_for_name("张女士"), "patient-zhang")
        self.assertEqual(patient_id_for_name("马先生"), "patient-ma")
        self.assertEqual(patient_id_for_name("李女士"), "patient-li")
        self.assertEqual(patient_id_for_name("匿名患者"), "unassigned")
        self.assertEqual(patient_id_for_name(None), "unassigned")

    def test_migration_moves_report_and_session_together_and_is_idempotent(self):
        from scripts.migrate_patient_ownership import migrate_patient_ownership

        state = self.repository.get_or_create_session("session-a", "demo-zhang")
        state["follow_up_answers"].append({"question": "多久？", "answer": "半年"})
        self.repository.save_session_state(state)
        self.repository.save_report(
            "demo-zhang",
            {
                "record_id": "record-a",
                "session_id": "session-a",
                "patient_name": "张女士",
            },
        )

        result = migrate_patient_ownership(self.repository)
        again = migrate_patient_ownership(self.repository)

        self.assertEqual(result.updated_reports, 1)
        self.assertEqual(result.updated_sessions, 1)
        self.assertEqual(again.updated_reports, 0)
        self.assertIsNotNone(
            self.repository.get_patient_report("patient-zhang", "record-a")
        )
        self.assertEqual(
            self.repository.get_or_create_session("session-a", "patient-zhang")[
                "patient_id"
            ],
            "patient-zhang",
        )
        with self.session_factory() as database:
            self.assertEqual(database.query(FollowUpAnswer).count(), 1)

    def test_dry_run_reports_changes_without_writing(self):
        from scripts.migrate_patient_ownership import migrate_patient_ownership

        self.repository.get_or_create_session("session-x", "demo-zhang")
        self.repository.save_report(
            "demo-zhang",
            {
                "record_id": "record-x",
                "session_id": "session-x",
                "patient_name": "马先生",
            },
        )

        result = migrate_patient_ownership(self.repository, dry_run=True)

        self.assertEqual(result.updated_reports, 1)
        self.assertIsNotNone(
            self.repository.get_patient_report("demo-zhang", "record-x")
        )
        self.assertIsNone(self.repository.get_patient_report("patient-ma", "record-x"))


if __name__ == "__main__":
    unittest.main()
