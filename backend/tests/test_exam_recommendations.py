import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exam_recommendations import build_recommended_exams
from intake_execution import blank_field_states


class ExamRecommendationTests(unittest.TestCase):
    def test_obesity_intake_recommends_small_core_set_not_full_package(self):
        states = blank_field_states({"pregnancy_applicable": False})
        states["height_weight"].update({"status": "confirmed", "evidence": ["身高165厘米，体重85公斤"]})
        exams = build_recommended_exams(states, red_flags=[])
        self.assertGreaterEqual(len(exams), 1)
        self.assertLessEqual(len(exams), 3)
        self.assertIn("肝肾功能", exams[0]["name"])
        self.assertTrue(all("price" not in item for item in exams))

    def test_metabolic_risk_adds_glycated_hemoglobin(self):
        states = blank_field_states({"pregnancy_applicable": False})
        states["important_history"].update({"status": "confirmed", "evidence": ["有糖尿病家族史"]})
        names = [item["name"] for item in build_recommended_exams(states, red_flags=[])]
        self.assertIn("糖化血红蛋白", names)

    def test_red_flag_does_not_return_routine_exam_package(self):
        states = blank_field_states({})
        self.assertEqual(build_recommended_exams(states, red_flags=["胸痛"]), [])

    def test_every_exam_carries_required_metadata_fields(self):
        states = blank_field_states({"pregnancy_applicable": False})
        states["height_weight"].update({"status": "confirmed", "evidence": ["身高165厘米，体重85公斤"]})
        exams = build_recommended_exams(states, red_flags=[])
        self.assertGreaterEqual(len(exams), 1)
        for item in exams:
            for key in ("name", "reason", "trigger", "priority", "source", "rule_version", "precautions"):
                self.assertIn(key, item)
                self.assertTrue(item[key])
            # 患者结果视图仍依赖 type 与 department
            self.assertIn("type", item)
            self.assertIn("department", item)

    def test_exam_source_and_rule_version_reference_guideline(self):
        states = blank_field_states({"pregnancy_applicable": False})
        exams = build_recommended_exams(states, red_flags=[])
        self.assertTrue(exams)
        for item in exams:
            self.assertEqual(item["rule_version"], "adult-obesity-intake-v1")
            self.assertIn("肥胖症诊疗指南", item["source"])

    def test_metabolic_history_triggers_glycated_hemoglobin_with_trigger(self):
        states = blank_field_states({"pregnancy_applicable": False})
        states["important_history"].update({"status": "confirmed", "evidence": ["有糖尿病家族史"]})
        exams = build_recommended_exams(states, red_flags=[])
        glycated = next(item for item in exams if item["name"] == "糖化血红蛋白")
        self.assertTrue(glycated["trigger"])

    def test_missing_data_produces_no_diagnosis_wording(self):
        states = blank_field_states({"pregnancy_applicable": False})
        exams = build_recommended_exams(states, red_flags=[])
        for item in exams:
            self.assertNotIn("确诊", item["reason"])
            self.assertNotIn("诊断", item["reason"])


if __name__ == "__main__":
    unittest.main()
