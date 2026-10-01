import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base


class PatientDirectoryTests(unittest.TestCase):
    def setUp(self):
        from repository import SqlAlchemyIntakeRepository

        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.repository = SqlAlchemyIntakeRepository(
            sessionmaker(bind=self.engine, expire_on_commit=False)
        )

    def tearDown(self):
        self.engine.dispose()

    def test_seed_demo_patients_is_idempotent(self):
        from patient_directory import DEMO_PATIENTS, seed_demo_patients

        seed_demo_patients(self.repository)
        seed_demo_patients(self.repository)

        patients = self.repository.list_patients()
        self.assertEqual([item["patient_id"] for item in patients], list(DEMO_PATIENTS))
        self.assertEqual(patients[0]["display_name"], "张女士")
        self.assertEqual(len(patients), 4)

    def test_patient_sessions_never_cross_patient_boundary(self):
        self.repository.ensure_patient("patient-a", "患者甲")
        self.repository.ensure_patient("patient-b", "患者乙")
        session_a = self.repository.get_or_create_session("session-a", "patient-a")
        session_a.update({"open_answer": "最近体重增加", "phase": "follow_up"})
        self.repository.save_session_state(session_a, expected_version=session_a["version"])
        self.repository.get_or_create_session("session-b", "patient-b")

        items = self.repository.list_patient_sessions("patient-a")

        self.assertEqual([item["session_id"] for item in items], ["session-a"])
        self.assertTrue(all(item["patient_id"] == "patient-a" for item in items))

    def test_doctor_session_list_hides_empty_shell_sessions(self):
        self.repository.ensure_patient("patient-a", "患者甲")
        self.repository.get_or_create_session("empty-session", "patient-a")
        active = self.repository.get_or_create_session("active-session", "patient-a")
        active.update({"open_answer": "近半年体重增加", "phase": "follow_up"})
        self.repository.save_session_state(active, expected_version=active["version"])

        items = self.repository.list_patient_sessions("patient-a")

        self.assertEqual([item["session_id"] for item in items], ["active-session"])

    def test_doctor_session_list_hides_session_whose_report_was_soft_deleted(self):
        self.repository.ensure_patient("patient-a", "患者甲")
        self.repository.get_or_create_session("deleted-report-session", "patient-a")
        record = self.repository.save_report(
            "patient-a", {"session_id": "deleted-report-session", "markdown_table": "表"}
        )
        self.repository.soft_delete_report("patient-a", record["record_id"])

        items = self.repository.list_patient_sessions("patient-a")

        self.assertEqual([item["session_id"] for item in items], [])

    def test_get_patient_returns_none_for_unknown_patient(self):
        self.assertIsNone(self.repository.get_patient("missing"))


if __name__ == "__main__":
    unittest.main()
