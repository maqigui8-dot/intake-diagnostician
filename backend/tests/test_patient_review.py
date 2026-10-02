import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intake_execution import PATIENT_CORE_FIELD_KEYS
from intake_flow import (
    complete_intake_session,
    correct_patient_field,
    get_intake_state,
    intake_sessions,
    set_baseline,
    submit_open_answer,
)
from intake_views import build_patient_state


class PatientReviewTests(unittest.TestCase):
    def setUp(self):
        intake_sessions.clear()

    def _completed_session(self):
        set_baseline("review-a", {
            "age": 35, "sex": "male", "height_cm": 175, "weight_kg": 90,
            "measured_at": "2026-10-01",
        })
        submit_open_answer("review-a", "最近体重增加，想改善体重")
        session = intake_sessions.get("review-a")
        for key in PATIENT_CORE_FIELD_KEYS:
            if session["field_states"][key]["status"] != "not_applicable":
                session["field_states"][key].update({"status": "confirmed", "evidence": ["已回答"]})
        session["field_states"]["medications"]["evidence"] = ["降压药"]
        session["follow_up_answers"].append({
            "question": "您目前正在使用哪些药物？", "answer": "降压药", "question_key": "medications",
        })
        intake_sessions.save(session)
        complete_intake_session("review-a")
        return intake_sessions.get("review-a")

    def test_correction_rebuilds_report_and_preserves_original_answer(self):
        self._completed_session()

        state = correct_patient_field("review-a", "medications", "目前没有服用药物")

        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["field_states"]["medications"]["evidence"], ["目前没有服用药物"])
        self.assertEqual(state["follow_up_answers"][0]["answer"], "降压药")
        self.assertIn("| 当前用药与保健品 | 目前没有服用药物 |", state["report_markdown"])
        correction = state["patient_corrections"][-1]
        self.assertEqual(correction["previous"], "降压药")
        self.assertEqual(correction["updated"], "目前没有服用药物")

    def test_unknown_correction_returns_to_incomplete_state(self):
        self._completed_session()

        state = correct_patient_field("review-a", "medications", "不清楚")

        self.assertEqual(state["phase"], "incomplete")
        self.assertIn("medications", state["blocking_keys"])

    def test_red_flag_and_unfinished_session_cannot_be_corrected_here(self):
        self._completed_session()
        with self.assertRaisesRegex(ValueError, "不可在此修改"):
            correct_patient_field("review-a", "red_flags", "没有")

        set_baseline("review-b", {
            "age": 35, "sex": "male", "height_cm": 175, "weight_kg": 90,
            "measured_at": "2026-10-01",
        })
        with self.assertRaisesRegex(ValueError, "仅在问诊结束后"):
            correct_patient_field("review-b", "medications", "没有")

    def test_patient_state_exposes_only_five_review_fields(self):
        state = self._completed_session()

        public = build_patient_state(get_intake_state("review-a"))

        fields = {item["field_key"]: item for item in public["review_fields"]}
        self.assertEqual(set(fields), {"main_goal", "onset_course", "allergies", "medications", "important_history"})
        self.assertEqual(fields["medications"]["value"], "降压药")
        self.assertNotIn("field_states", public)

    def test_stopped_draft_exposes_blocker_and_can_be_completed_by_patient(self):
        self._completed_session()
        session = intake_sessions.get("review-a")
        session["field_states"]["stool_urine"].update({
            "status": "unavailable", "evidence": [], "attempts": 2,
        })
        intake_sessions.save(session)
        complete_intake_session("review-a")

        draft = build_patient_state(get_intake_state("review-a"))
        self.assertEqual(draft["phase"], "incomplete")
        self.assertIn("stool_urine", {item["field_key"] for item in draft["blocking_fields"]})
        self.assertIn("stool_urine", {item["field_key"] for item in draft["review_fields"]})
        self.assertFalse(draft["can_continue"])

        corrected = correct_patient_field("review-a", "stool_urine", "没有")
        self.assertEqual(corrected["phase"], "completed")
        self.assertEqual(corrected["field_states"]["stool_urine"]["evidence"], ["没有"])
        self.assertEqual(corrected["field_states"]["stool_urine"]["status"], "confirmed")

    def test_draft_correction_rejects_unrelated_text(self):
        self._completed_session()
        session = intake_sessions.get("review-a")
        session["field_states"]["stool_urine"].update({
            "status": "unavailable", "evidence": [], "attempts": 2,
        })
        intake_sessions.save(session)
        complete_intake_session("review-a")

        with self.assertRaisesRegex(ValueError, "当前资料项"):
            correct_patient_field("review-a", "stool_urine", "今天心情很好")
        self.assertEqual(get_intake_state("review-a")["phase"], "incomplete")

    def test_draft_can_revalidate_same_text_that_was_previously_left_partial(self):
        self._completed_session()
        session = intake_sessions.get("review-a")
        session["field_states"]["stool_urine"].update({
            "status": "partial", "evidence": ["没有"], "attempts": 2,
        })
        intake_sessions.save(session)
        complete_intake_session("review-a")

        corrected = correct_patient_field("review-a", "stool_urine", "没有")
        self.assertEqual(corrected["phase"], "completed")
        self.assertEqual(corrected["field_states"]["stool_urine"]["status"], "confirmed")

    def test_existing_danger_signal_cannot_be_cleared_by_draft_correction(self):
        self._completed_session()
        session = intake_sessions.get("review-a")
        session["field_states"]["red_flags"].update({
            "status": "unavailable", "evidence": [], "attempts": 2,
        })
        session["safety_alerts"] = ["胸痛"]
        intake_sessions.save(session)
        complete_intake_session("review-a")

        with self.assertRaisesRegex(ValueError, "危险信号"):
            correct_patient_field("review-a", "red_flags", "没有")
        self.assertEqual(get_intake_state("review-a")["safety_alerts"], ["胸痛"])

    def test_applicable_pregnancy_gap_accepts_explicit_negative_correction(self):
        set_baseline("review-pregnancy", {
            "age": 35, "sex": "female", "height_cm": 165, "weight_kg": 82,
            "measured_at": "2026-10-01",
        })
        submit_open_answer("review-pregnancy", "最近体重增加")
        session = intake_sessions.get("review-pregnancy")
        for key in PATIENT_CORE_FIELD_KEYS:
            if session["field_states"][key]["status"] != "not_applicable":
                session["field_states"][key].update({"status": "confirmed", "evidence": ["已回答"]})
        session["field_states"]["pregnancy"].update({
            "status": "unavailable", "evidence": [], "attempts": 2,
        })
        intake_sessions.save(session)
        complete_intake_session("review-pregnancy")

        corrected = correct_patient_field("review-pregnancy", "pregnancy", "没有")
        self.assertEqual(corrected["phase"], "completed")
        self.assertEqual(corrected["field_states"]["pregnancy"]["evidence"], ["没有"])

    def test_draft_public_copy_and_report_do_not_promise_in_clinic_verification(self):
        self._completed_session()
        session = intake_sessions.get("review-a")
        session["field_states"]["stool_urine"].update({
            "status": "unavailable", "evidence": [], "attempts": 2,
        })
        intake_sessions.save(session)
        complete_intake_session("review-a")

        public = build_patient_state(get_intake_state("review-a"))
        self.assertIn("诊前资料草稿", public["report_markdown"])
        self.assertNotIn("诊中", public["report_markdown"])
        self.assertIn("尚未提供", public["report_markdown"])
        self.assertNotIn("诊中", public["stop_reason_public"])


if __name__ == "__main__":
    unittest.main()
