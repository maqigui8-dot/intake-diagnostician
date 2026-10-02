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
        self.assertNotIn("context", public)

    def test_patient_state_uses_public_stop_reason(self):
        state = get_intake_state("session-a")
        state.update({"phase": "completed", "stop_reason": "safety_limit"})
        public = build_patient_state(state)
        self.assertEqual(public["stop_reason_public"], "在线追问已结束，未确认信息仍保留在草稿中。")

    def test_patient_state_shows_core_progress_without_doctor_details(self):
        state = get_intake_state("session-a")
        state["context"] = {"baseline_confirmed": True, "pregnancy_applicable": False}
        state["field_states"]["pregnancy"]["status"] = "not_applicable"
        state["field_states"]["allergies"]["status"] = "confirmed"

        public = build_patient_state(state)

        self.assertEqual(public["progress"], {
            "core_completed": 1,
            "core_total": 16,
            "remaining_count": 15,
            "pending_count": 15,
            "unavailable_count": 0,
            "ready": False,
        })
        self.assertNotIn("blocking_keys", public)

    def test_patient_progress_does_not_count_unresolved_conflict(self):
        state = get_intake_state("session-a")
        state["context"] = {"baseline_confirmed": True, "pregnancy_applicable": False}
        state["field_states"]["pregnancy"]["status"] = "not_applicable"
        state["field_states"]["allergies"].update({
            "status": "confirmed",
            "conflicts": [{"evidence": "前后说法不一致", "resolved": False}],
        })

        public = build_patient_state(state)

        self.assertEqual(public["progress"]["core_completed"], 0)
        self.assertEqual(public["progress"]["remaining_count"], 16)

    def test_patient_progress_separates_unavailable_from_pending(self):
        state = get_intake_state("session-a")
        state["context"] = {"baseline_confirmed": True, "pregnancy_applicable": False}
        state["field_states"]["pregnancy"]["status"] = "not_applicable"
        state["field_states"]["allergies"]["status"] = "unavailable"

        public = build_patient_state(state)

        self.assertEqual(public["progress"]["unavailable_count"], 1)
        self.assertEqual(public["progress"]["pending_count"], 15)

    def test_protective_incomplete_state_is_not_serialized_as_complete(self):
        state = get_intake_state("session-a")
        state.update({"phase": "incomplete", "stop_reason": "patient_unavailable", "report_markdown": "未完整档案"})
        for field in state["field_states"].values():
            field["status"] = "unavailable"

        public = build_patient_state(state)

        self.assertFalse(public["is_complete"])
        self.assertEqual(public["phase"], "incomplete")
        self.assertEqual(public["report_markdown"], "未完整档案")
        self.assertFalse(public["can_continue"])

    def test_incomplete_state_can_continue_only_when_a_core_question_remains(self):
        state = get_intake_state("session-a")
        state.update({"phase": "incomplete", "stop_reason": "threshold_recheck_incomplete"})
        public = build_patient_state(state)
        self.assertTrue(public["can_continue"])

        for field in state["field_states"].values():
            field["status"] = "unavailable"
        public = build_patient_state(state)
        self.assertFalse(public["can_continue"])

    def test_stale_threshold_reached_resident_is_serialized_as_incomplete(self):
        resident = intake_sessions.get("stale-threshold")
        resident.update({"phase": "completed", "stop_reason": "threshold_reached"})

        public = build_patient_state(intake_sessions.get("stale-threshold"))

        self.assertEqual(public["phase"], "incomplete")
        self.assertFalse(public["is_complete"])
        self.assertIn("仍有关键项目未确认", public["stop_reason_public"])
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

    def test_doctor_summary_exposes_baseline_assessment_with_bmi_and_rule_hint(self):
        state = get_intake_state("session-a")
        state["baseline"] = {
            "age": 32, "sex": "female", "height_cm": 170.0, "weight_kg": 81.0,
            "waist_cm": 88.0, "hip_cm": None, "measured_at": "2026-08-01",
        }
        state["bmi_assessment"] = {
            "bmi": 28.0,
            "bmi_grade": "轻度肥胖范围",
            "diagnosis_copy": "达到成人肥胖范围，待医生确认",
        }

        summary = build_doctor_summary(state)

        self.assertEqual(summary["baseline_assessment"]["age"], 32)
        self.assertEqual(summary["baseline_assessment"]["bmi"], 28.0)
        self.assertEqual(summary["baseline_assessment"]["bmi_grade"], "轻度肥胖范围")
        self.assertIn("待医生确认", summary["baseline_assessment"]["rule_hint"])

    def test_doctor_summary_exposes_four_layer_scores(self):
        summary = build_doctor_summary(get_intake_state("session-a"))
        layers = summary["layer_execution"]
        for key in ("baseline", "risk", "tcm", "safety"):
            self.assertIn(key, layers)
            self.assertIn("score", layers[key])
        self.assertIn("threshold", layers["risk"])
        self.assertIn("threshold", layers["tcm"])
        self.assertIn("threshold", layers["safety"])

    def test_doctor_summary_exposes_readiness_from_decision_explanation(self):
        summary = build_doctor_summary(get_intake_state("session-a"))

        self.assertEqual(summary["readiness_summary"], summary["decision_explanation"]["readiness"])

    def test_doctor_summary_groups_fields_into_six_sections(self):
        summary = build_doctor_summary(get_intake_state("session-a"))
        expected = [
            "基础测量与肥胖范围",
            "肥胖病程与可能病因",
            "相关疾病风险",
            "生活方式与心理情况",
            "中医诊前资料",
            "待医生确认",
        ]
        for section in expected:
            self.assertIn(section, summary["field_groups"])

        pending = {item["field_key"] for item in summary["field_groups"]["待医生确认"]}
        self.assertIn("allergies", pending)
        self.assertIn("red_flags", pending)

        tcm = {item["field_key"] for item in summary["field_groups"]["中医诊前资料"]}
        self.assertIn("tongue", tcm)
        self.assertIn("appetite_thirst", tcm)

    def test_patient_state_omits_doctor_only_structures(self):
        public = build_patient_state(get_intake_state("session-a"))
        for key in ("baseline_assessment", "layer_execution", "field_groups", "execution", "blocking_keys"):
            self.assertNotIn(key, public)


if __name__ == "__main__":
    unittest.main()
