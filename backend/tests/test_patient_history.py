import unittest
from pathlib import Path
import sys

import patient_history

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from patient_history import (
    DEMO_PATIENT_ID,
    belongs_to_patient,
    make_history_item,
    make_patient_history_detail,
)


class PatientHistoryTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "record_id": "record-1",
            "patient_id": DEMO_PATIENT_ID,
            "created_at": "2026-08-23T10:30:00",
            "collected_info": {"开放描述": "最近半年体重增加十斤"},
            "markdown_table": "## 诊前档案\n\n已整理的问诊内容",
            "follow_up_answers": [{"question": "睡眠如何？", "answer": "容易醒"}],
            "recommended_exams": [{"name": "肝功能三项", "priority": "routine"}],
            "doctor_summary": {"execution": {"total_score": 88}},
            "rule_version": "internal-only",
        }

    def test_only_current_patient_records_are_in_scope(self):
        self.assertTrue(belongs_to_patient(self.record, DEMO_PATIENT_ID))
        self.assertFalse(belongs_to_patient({"record_id": "legacy"}, DEMO_PATIENT_ID))
        self.assertFalse(belongs_to_patient({"patient_id": "someone-else"}, DEMO_PATIENT_ID))

    def test_history_item_has_patient_facing_summary_only(self):
        item = make_history_item(self.record)

        self.assertEqual(item["record_id"], "record-1")
        self.assertEqual(item["primary_concern"], "最近半年体重增加十斤")
        self.assertEqual(item["status"], "资料已整理")
        self.assertNotIn("doctor_summary", item)
        self.assertNotIn("patient_id", item)

    def test_history_detail_excludes_doctor_only_fields(self):
        detail = make_patient_history_detail(self.record)

        self.assertEqual(detail["follow_up_answers"][0]["answer"], "容易醒")
        self.assertEqual(detail["recommended_exams"][0]["name"], "肝功能三项")
        self.assertNotIn("doctor_summary", detail)
        self.assertNotIn("rule_version", detail)
        self.assertNotIn("patient_id", detail)

    def test_find_record_for_session_is_scoped_to_current_patient(self):
        finder = getattr(patient_history, "find_record_for_session", None)
        self.assertIsNotNone(finder)
        records = [
            {**self.record, "session_id": "session-a"},
            {**self.record, "record_id": "record-2", "patient_id": "someone-else", "session_id": "session-b"},
        ]

        self.assertEqual(finder(records, DEMO_PATIENT_ID, "session-a")["record_id"], "record-1")
        self.assertIsNone(finder(records, DEMO_PATIENT_ID, "session-b"))
        self.assertIsNone(finder(records, DEMO_PATIENT_ID, ""))


if __name__ == "__main__":
    unittest.main()
