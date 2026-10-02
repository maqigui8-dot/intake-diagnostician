import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from db import Base
from intake_flow import configure_intake_repository, intake_sessions, set_baseline
from repository import SqlAlchemyIntakeRepository
from repository import ArchivedSession, ConcurrentSessionUpdate, DeletedReport


class DatabaseApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.repository = SqlAlchemyIntakeRepository(factory)
        configure_intake_repository(self.repository)
        main.configure_report_repository(self.repository)

    async def asyncTearDown(self):
        main.configure_report_repository(None)
        configure_intake_repository(None)
        self.engine.dispose()

    async def test_save_record_is_idempotent_in_database(self):
        set_baseline(
            "complete-a",
            {
                "age": 35,
                "sex": "male",
                "height_cm": 175,
                "weight_kg": 90,
                "measured_at": "2026-09-16",
            },
        )
        state = intake_sessions.get("complete-a")
        for field in state["field_states"].values():
            if field["status"] != "not_applicable":
                field["status"] = "confirmed"
        state.update({"phase": "completed", "stop_reason": "threshold_reached"})
        intake_sessions.save(state)

        first = await main.save_record(main.SaveRecordRequest(session_id="complete-a"))
        second = await main.save_record(main.SaveRecordRequest(session_id="complete-a"))

        self.assertEqual(first["record_id"], second["record_id"])
        self.assertEqual(len(self.repository.list_patient_reports("demo-zhang")), 1)

    async def test_concurrent_update_is_mapped_to_http_409(self):
        response = await main.handle_concurrent_session_update(
            None, ConcurrentSessionUpdate("stale")
        )

        self.assertEqual(response.status_code, 409)
        self.assertNotIn("stale", response.body.decode("utf-8"))

    async def test_unfinished_sessions_can_be_listed_and_archived(self):
        set_baseline(
            "draft-a",
            {
                "age": 35,
                "sex": "male",
                "height_cm": 175,
                "weight_kg": 90,
                "measured_at": "2026-09-16",
            },
        )

        items = await main.list_unfinished_intake_sessions()
        self.assertEqual([item["session_id"] for item in items], ["draft-a"])

        first = await main.archive_intake_session("draft-a")
        second = await main.archive_intake_session("draft-a")

        self.assertEqual(first, second)
        self.assertEqual(await main.list_unfinished_intake_sessions(), [])

    async def test_archived_session_is_mapped_to_http_410(self):
        response = await main.handle_archived_session(None, ArchivedSession("private detail"))

        self.assertEqual(response.status_code, 410)
        self.assertNotIn("private detail", response.body.decode("utf-8"))

    async def test_completed_record_can_be_soft_deleted(self):
        self.repository.get_or_create_session("delete-session", "demo-zhang")
        self.repository.save_report(
            "demo-zhang",
            {"record_id": "delete-record", "session_id": "delete-session", "markdown_table": "报告"},
        )

        first = await main.delete_patient_record("delete-record")
        second = await main.delete_patient_record("delete-record")

        self.assertEqual(first, second)
        self.assertEqual(await main.list_patient_records(), [])

    async def test_deleted_report_is_mapped_to_http_410(self):
        response = await main.handle_deleted_report(None, DeletedReport("private detail"))

        self.assertEqual(response.status_code, 410)
        self.assertNotIn("private detail", response.body.decode("utf-8"))

    async def test_delete_missing_record_returns_404(self):
        from fastapi import HTTPException

        with self.assertRaises(HTTPException) as raised:
            await main.delete_patient_record("missing")

        self.assertEqual(raised.exception.status_code, 404)

    async def test_incomplete_save_tells_patient_to_continue(self):
        from fastapi import HTTPException

        self.repository.get_or_create_session("unfinished-save", "demo-zhang")

        with self.assertRaises(HTTPException) as raised:
            await main.save_record(main.SaveRecordRequest(session_id="unfinished-save"))

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("返回草稿补充", raised.exception.detail)
        self.assertNotIn("由医生继续", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
