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


if __name__ == "__main__":
    unittest.main()
