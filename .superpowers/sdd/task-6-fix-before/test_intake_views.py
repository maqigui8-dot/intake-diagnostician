import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intake_flow import get_intake_state, intake_sessions
from intake_views import build_doctor_summary, build_patient_state


class IntakeViewTests(unittest.TestCase):
    def setUp(self):
        intake_sessions.clear()

    def test_patient_state_excludes_internal_execution_fields(self):
        public = build_patient_state(get_intake_state("session-a"))
        encoded = json.dumps(public, ensure_ascii=False)
        self.assertNotIn("execution", public)
        self.assertNotIn("field_states", public)
        self.assertNotIn("blocking_keys", encoded)
        self.assertNotIn("question_key", encoded)

    def test_patient_state_exposes_baseline_and_bmi_assessment(self):
        state = get_intake_state("session-a")
        state["baseline"] = {"age": 32, "sex": "female", "height_cm": 170.0, "weight_kg": 81.0}
        state["bmi_assessment"] = {
            "bmi": 28.0,
            "bmi_grade": "轻度肥胖范围",
            "diagnosis_copy": "达到成人肥胖范围，待医生确认",
        }

        public = build_patient_state(state)

        self.assertEqual(public["baseline"], state["baseline"])
        self.assertEqual(public["bmi_assessment"]["bmi"], 28.0)
        self.assertEqual(public["bmi_assessment"]["diagnosis_copy"], "达到成人肥胖范围，待医生确认")
        self.assertNotIn("execution", public)
        self.assertNotIn("field_states", public)
        self.assertNotIn("blocking_keys", public)

    def test_patient_state_uses_public_stop_reason(self):
        state = get_intake_state("session-a")
        state.update({"phase": "completed", "stop_reason": "safety_limit"})
        public = build_patient_state(state)
        self.assertEqual(public["stop_reason_public"], "历史问诊已保护性结束，剩余信息请在诊中补充。")

    def test_protective_incomplete_state_is_not_serialized_as_complete(self):
        state = get_intake_state("session-a")
        state.update({"phase": "incomplete", "stop_reason": "patient_unavailable", "report_markdown": "未完整档案"})

        public = build_patient_state(state)

        self.assertFalse(public["is_complete"])
        self.assertEqual(public["phase"], "incomplete")
        self.assertEqual(public["report_markdown"], "未完整档案")

    def test_stale_threshold_reached_resident_is_serialized_as_incomplete(self):
        resident = intake_sessions.get("stale-threshold")
        resident.update({"phase": "completed", "stop_reason": "threshold_reached"})

        public = build_patient_state(intake_sessions.get("stale-threshold"))

        self.assertEqual(public["phase"], "incomplete")
        self.assertFalse(public["is_complete"])
        self.assertIn("继续补充", public["stop_reason_public"])
        self.assertNotIn("已整理完成", public["stop_reason_public"])

    def test_doctor_summary_contains_scores_evidence_and_rule_version(self):
        state = get_intake_state("session-a")
        state["field_states"]["allergies"].update({
            "status": "confirmed", "evidence": ["没有过敏"], "confidence": 0.98,
        })
        summary = build_doctor_summary(state)
        self.assertEqual(summary["access_scope"], "prototype_doctor_view")
        self.assertIn("total_score", summary["execution"])
        self.assertEqual(summary["safety_fields"][0]["evidence"], ["没有过敏"])
        self.assertEqual(summary["rule_version"], "adult-obesity-intake-v1")

    def test_doctor_summary_preserves_legacy_metabolic_state_for_audit(self):
        state = get_intake_state("session-a")
        state["field_states"]["metabolic_tests"] = {
            "status": "confirmed", "evidence": ["旧版代谢检查已回答"], "confidence": 0.9,
            "attempts": 1, "conflicts": [], "audit": [{"turn": 1}],
        }

        summary = build_doctor_summary(state)

        self.assertEqual(summary["legacy_fields"]["metabolic_tests"]["evidence"], ["旧版代谢检查已回答"])
        self.assertEqual(summary["legacy_fields"]["metabolic_tests"]["audit"], [{"turn": 1}])


if __name__ == "__main__":
    unittest.main()
