import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from db import Base
from intake_execution import PATIENT_CORE_FIELD_KEYS
from intake_flow import configure_intake_repository, intake_sessions, set_baseline, submit_open_answer, complete_intake_session
from patient_directory import seed_demo_patients
from repository import SqlAlchemyIntakeRepository


class MultiPatientApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.repository = SqlAlchemyIntakeRepository(
            sessionmaker(bind=self.engine, expire_on_commit=False)
        )
        seed_demo_patients(self.repository)
        configure_intake_repository(self.repository)
        main.configure_report_repository(self.repository)

    async def asyncTearDown(self):
        main.configure_report_repository(None)
        configure_intake_repository(None)
        self.engine.dispose()

    async def test_patient_cannot_read_another_patients_record(self):
        self.repository.get_or_create_session("zhang-session", "patient-zhang")
        self.repository.save_report(
            "patient-zhang",
            {"record_id": "zhang-record", "session_id": "zhang-session"},
        )

        with self.assertRaises(main.HTTPException) as error:
            await main.get_scoped_patient_record("patient-ma", "zhang-record")

        self.assertEqual(error.exception.status_code, 404)

    async def test_session_creation_requires_known_explicit_patient(self):
        result = await main.create_scoped_intake_session(
            "patient-ma", main.SessionCreateRequest(session_id="ma-session")
        )
        self.assertEqual(result["session_id"], "ma-session")
        self.assertEqual(self.repository.get_session_owner("ma-session"), "patient-ma")
        with self.assertRaises(main.HTTPException) as error:
            await main.create_scoped_intake_session(
                "missing", main.SessionCreateRequest(session_id="bad")
            )
        self.assertEqual(error.exception.status_code, 404)

    async def test_patient_only_app_has_no_doctor_data_routes(self):
        paths = {route.path for route in main.app.routes}
        self.assertFalse(any(path.startswith("/api/doctor/") for path in paths))
        self.assertFalse(any(path.endswith("/doctor-summary") for path in paths))

    async def test_active_routes_do_not_publish_legacy_anonymous_patient_data(self):
        paths = {route.path for route in main.app.routes}
        self.assertNotIn("/api/chat", paths)
        self.assertNotIn("/api/save_record", paths)
        self.assertNotIn("/api/records", paths)
        self.assertNotIn("/api/patient/records", paths)
        self.assertFalse(any(path.startswith("/api/intake/session/") for path in paths))
        self.assertIn("/api/patients/{patient_id}/sessions/{session_id}/save", paths)

    async def test_scoped_save_requires_owner_and_explicit_confirmation(self):
        self.repository.get_or_create_session("ma-save", "patient-ma")
        with self.assertRaises(main.HTTPException) as wrong_owner:
            await main.save_scoped_patient_record(
                "patient-zhang", "ma-save", main.PatientSaveRequest(patient_confirmed=True),
            )
        self.assertEqual(wrong_owner.exception.status_code, 404)

        with self.assertRaises(main.HTTPException) as unconfirmed:
            await main.save_scoped_patient_record(
                "patient-ma", "ma-save", main.PatientSaveRequest(patient_confirmed=False),
            )
        self.assertEqual(unconfirmed.exception.status_code, 400)

    async def test_patient_can_correct_then_confirm_save_once(self):
        await main.create_scoped_intake_session(
            "patient-ma", main.SessionCreateRequest(session_id="review-save"),
        )
        set_baseline("review-save", {
            "age": 32, "sex": "male", "height_cm": 170, "weight_kg": 83,
            "measured_at": "2026-10-01",
        }, "patient-ma")
        submit_open_answer("review-save", "最近体重增加", "patient-ma")
        session = intake_sessions.get("review-save", "patient-ma")
        for key in PATIENT_CORE_FIELD_KEYS:
            if session["field_states"][key]["status"] != "not_applicable":
                session["field_states"][key].update({"status": "confirmed", "evidence": ["已回答"]})
        session["field_states"]["medications"]["evidence"] = ["降压药"]
        intake_sessions.save(session)
        complete_intake_session("review-save")

        corrected = await main.correct_scoped_intake_field(
            "patient-ma", "review-save",
            main.IntakeCorrectionRequest(field_key="medications", value="目前没有服用药物"),
        )
        first = await main.save_scoped_patient_record(
            "patient-ma", "review-save", main.PatientSaveRequest(patient_confirmed=True),
        )
        second = await main.save_scoped_patient_record(
            "patient-ma", "review-save", main.PatientSaveRequest(patient_confirmed=True),
        )

        self.assertEqual(
            next(item["value"] for item in corrected["review_fields"] if item["field_key"] == "medications"),
            "目前没有服用药物",
        )
        self.assertEqual(first["record_id"], second["record_id"])
        self.assertIn("目前没有服用药物", self.repository.get_patient_report("patient-ma", first["record_id"])["markdown_table"])

    async def test_correction_rejects_another_patients_session(self):
        self.repository.get_or_create_session("zhang-review", "patient-zhang")

        with self.assertRaises(main.HTTPException) as error:
            await main.correct_scoped_intake_field(
                "patient-ma", "zhang-review",
                main.IntakeCorrectionRequest(field_key="medications", value="没有用药"),
            )

        self.assertEqual(error.exception.status_code, 404)

    async def test_correction_rejects_already_saved_record(self):
        self.repository.get_or_create_session("saved-review", "patient-zhang")
        self.repository.save_report("patient-zhang", {
            "record_id": "saved-review-record", "session_id": "saved-review",
        })

        with self.assertRaises(main.HTTPException) as error:
            await main.correct_scoped_intake_field(
                "patient-zhang", "saved-review",
                main.IntakeCorrectionRequest(field_key="medications", value="没有用药"),
            )

        self.assertEqual(error.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
