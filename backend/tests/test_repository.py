import unittest
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base


class RepositoryTests(unittest.TestCase):
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

    def test_session_round_trip_preserves_follow_up_state(self):
        state = self.repository.get_or_create_session("session-a", "patient-a")
        state.update({"phase": "follow_up", "turn": 2, "current_field_key": "allergies"})
        state["follow_up_answers"].append(
            {
                "question": "有药物过敏吗？",
                "answer": "没有",
                "question_key": "allergies",
                "question_kind": "required",
                "attempt_number": 1,
                "answer_quality": "provided",
                "created_at": "2026-09-16T10:00:00",
            }
        )

        self.repository.save_session_state(state)
        restored = self.repository.get_or_create_session("session-a", "patient-a")

        self.assertEqual(restored["phase"], "follow_up")
        self.assertEqual(restored["follow_up_answers"][0]["answer"], "没有")

    def test_report_save_is_idempotent_and_patient_scoped(self):
        self.repository.get_or_create_session("s1", "patient-a")
        first = self.repository.save_report(
            "patient-a",
            {"record_id": "record-a", "session_id": "s1", "markdown_table": "A"},
        )
        second = self.repository.save_report(
            "patient-a",
            {"record_id": "different", "session_id": "s1", "markdown_table": "B"},
        )

        self.assertEqual(first["record_id"], second["record_id"])
        self.assertEqual(second["markdown_table"], "B")
        self.assertIsNone(self.repository.get_patient_report("patient-b", "record-a"))
        self.assertEqual(len(self.repository.list_patient_reports("patient-a")), 1)

    def test_stale_version_is_rejected(self):
        from repository import ConcurrentSessionUpdate

        state = self.repository.get_or_create_session("versioned", "patient-a")
        self.repository.save_session_state(state, expected_version=1)

        with self.assertRaises(ConcurrentSessionUpdate):
            self.repository.save_session_state(state, expected_version=1)

    def test_unfinished_sessions_are_patient_scoped_meaningful_and_sorted(self):
        blank = self.repository.get_or_create_session("blank", "patient-a")
        older = self.repository.get_or_create_session("older", "patient-a")
        older.update({"baseline_confirmed": True, "phase": "open_intake"})
        self.repository.save_session_state(older)
        newer = self.repository.get_or_create_session("newer", "patient-a")
        newer.update({"baseline_confirmed": True, "phase": "follow_up", "open_answer": "最近体重增加", "turn": 2})
        newer["follow_up_answers"].append({"question": "多久了？", "answer": "三个月"})
        self.repository.save_session_state(newer)
        other = self.repository.get_or_create_session("other", "patient-b")
        other.update({"baseline_confirmed": True, "phase": "open_intake"})
        self.repository.save_session_state(other)

        from models import IntakeSessionModel
        with self.session_factory.begin() as database:
            old_row = database.get(IntakeSessionModel, "older")
            old_row.updated_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)

        items = self.repository.list_unfinished_sessions("patient-a")

        self.assertEqual([item["session_id"] for item in items], ["newer", "older"])
        self.assertEqual(items[0]["primary_concern"], "最近体重增加")
        self.assertEqual(items[0]["stage_label"], "第 2 轮补充")
        self.assertNotIn(blank["session_id"], [item["session_id"] for item in items])

    def test_unfinished_sessions_include_completed_awaiting_review_but_exclude_reported_and_archived(self):
        for session_id in ("active", "terminal", "reported", "archived"):
            state = self.repository.get_or_create_session(session_id, "patient-a")
            state.update({"baseline_confirmed": True, "phase": "open_intake"})
            self.repository.save_session_state(state)
        terminal = self.repository.get_or_create_session("terminal", "patient-a")
        terminal["phase"] = "completed"
        self.repository.save_session_state(terminal)
        self.repository.save_report("patient-a", {"record_id": "r1", "session_id": "reported"})
        self.repository.archive_session("patient-a", "archived")

        items = self.repository.list_unfinished_sessions("patient-a")
        self.assertEqual({item["session_id"] for item in items}, {"active", "terminal"})
        self.assertEqual(next(item for item in items if item["session_id"] == "terminal")["stage_label"], "待核对保存")

    def test_archive_is_idempotent_preserves_answers_and_blocks_restore(self):
        from models import AuditEvent, FollowUpAnswer, IntakeSessionModel
        from repository import ArchivedSession

        state = self.repository.get_or_create_session("archive-me", "patient-a")
        state.update({"baseline_confirmed": True, "phase": "follow_up", "open_answer": "需要继续"})
        state["follow_up_answers"].append({"question": "多久？", "answer": "半年"})
        self.repository.save_session_state(state)

        first = self.repository.archive_session("patient-a", "archive-me")
        second = self.repository.archive_session("patient-a", "archive-me")

        self.assertEqual(first["archived_at"], second["archived_at"])
        with self.session_factory() as database:
            self.assertIsNotNone(database.get(IntakeSessionModel, "archive-me").archived_at)
            self.assertEqual(len(database.scalars(select(FollowUpAnswer).where(FollowUpAnswer.session_id == "archive-me")).all()), 1)
            events = database.scalars(select(AuditEvent).where(AuditEvent.session_id == "archive-me", AuditEvent.event_type == "session_archived")).all()
            self.assertEqual(len(events), 1)
        with self.assertRaises(ArchivedSession):
            self.repository.get_or_create_session("archive-me", "patient-a")

    def test_archive_cannot_cross_patient_boundary(self):
        self.repository.get_or_create_session("private", "patient-a")

        with self.assertRaises(KeyError):
            self.repository.archive_session("patient-b", "private")

    def test_report_soft_delete_is_idempotent_hidden_and_preserves_related_data(self):
        from models import BaselineMeasurement, FollowUpAnswer, IntakeReport, IntakeSessionModel
        from repository import DeletedReport

        state = self.repository.get_or_create_session("report-session", "patient-a")
        state.update(
            {
                "baseline_confirmed": True,
                "phase": "completed",
                "baseline": {
                    "age": 35,
                    "sex": "male",
                    "height_cm": 175,
                    "weight_kg": 90,
                    "measured_at": "2026-09-17",
                },
                "open_answer": "想改善体重",
            }
        )
        state["follow_up_answers"].append({"question": "多久？", "answer": "半年"})
        self.repository.save_session_state(state)
        self.repository.save_report(
            "patient-a",
            {"record_id": "record-delete", "session_id": "report-session", "markdown_table": "报告"},
        )

        first = self.repository.soft_delete_report("patient-a", "record-delete")
        second = self.repository.soft_delete_report("patient-a", "record-delete")

        self.assertEqual(first, second)
        self.assertEqual(self.repository.list_patient_reports("patient-a"), [])
        with self.assertRaises(DeletedReport):
            self.repository.get_patient_report("patient-a", "record-delete")

        self.repository.save_report(
            "patient-a",
            {"record_id": "replacement", "session_id": "report-session", "markdown_table": "更新报告"},
        )
        with self.session_factory() as database:
            report = database.get(IntakeReport, "record-delete")
            self.assertIsNotNone(report.deleted_at)
            self.assertEqual(len(database.scalars(select(IntakeReport)).all()), 1)
            self.assertIsNotNone(database.get(IntakeSessionModel, "report-session"))
            self.assertIsNotNone(database.scalar(select(BaselineMeasurement).where(BaselineMeasurement.session_id == "report-session")))
            self.assertEqual(len(database.scalars(select(FollowUpAnswer).where(FollowUpAnswer.session_id == "report-session")).all()), 1)

    def test_report_soft_delete_cannot_cross_patient_boundary(self):
        self.repository.get_or_create_session("owned-session", "patient-a")
        self.repository.save_report(
            "patient-a",
            {"record_id": "owned-record", "session_id": "owned-session"},
        )

        with self.assertRaises(KeyError):
            self.repository.soft_delete_report("patient-b", "owned-record")


if __name__ == "__main__":
    unittest.main()
