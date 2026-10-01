import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from obesity_diagnosis import (
    calculate_bmi,
    classify_adult_bmi,
    evaluate_central_obesity,
    validate_baseline,
)


class ObesityDiagnosisTests(unittest.TestCase):
    def test_adult_bmi_and_grade(self):
        self.assertEqual(calculate_bmi(170, 81), 28.0)
        self.assertEqual(classify_adult_bmi(18.4), "体重过低")
        self.assertEqual(classify_adult_bmi(18.5), "体重正常")
        self.assertEqual(classify_adult_bmi(24.0), "超重")
        self.assertEqual(classify_adult_bmi(27.9), "超重")
        self.assertEqual(classify_adult_bmi(28.0), "轻度肥胖范围")
        self.assertEqual(classify_adult_bmi(32.5), "中度肥胖范围")
        self.assertEqual(classify_adult_bmi(37.5), "重度肥胖范围")
        self.assertEqual(classify_adult_bmi(50.0), "极重度肥胖范围")

    def test_central_obesity_uses_sex_specific_waist_threshold(self):
        self.assertTrue(evaluate_central_obesity("male", 90, None)["waist_reached"])
        self.assertFalse(evaluate_central_obesity("female", 84.9, None)["waist_reached"])
        self.assertTrue(evaluate_central_obesity("female", 85, None)["waist_reached"])

    def test_central_obesity_calculates_sex_specific_waist_hip_ratio(self):
        male = evaluate_central_obesity("male", 90, 100)
        female = evaluate_central_obesity("female", 85, 100)

        self.assertEqual(male["waist_hip_ratio"], 0.9)
        self.assertTrue(male["waist_hip_ratio_reached"])
        self.assertEqual(female["waist_hip_ratio"], 0.9)
        self.assertTrue(female["waist_hip_ratio_reached"])

    def test_waist_hip_ratio_compares_before_rounding(self):
        male = evaluate_central_obesity("male", 85, 100)

        self.assertEqual(male["waist_hip_ratio"], 0.9)
        self.assertFalse(male["waist_hip_ratio_reached"])

    def test_validate_baseline_normalizes_measurements_and_adds_safe_copy(self):
        result = validate_baseline({
            "age": "32",
            "sex": "female",
            "height_cm": "170",
            "weight_kg": "81",
            "waist_cm": "85",
            "hip_cm": "100",
            "measured_at": "2026-08-18",
        })

        self.assertEqual(result["age"], 32)
        self.assertEqual(result["sex"], "female")
        self.assertEqual(result["height_cm"], 170.0)
        self.assertEqual(result["weight_kg"], 81.0)
        self.assertEqual(result["bmi"], 28.0)
        self.assertEqual(result["bmi_grade"], "轻度肥胖范围")
        self.assertEqual(
            result["diagnosis_copy"],
            "当前BMI达到成人肥胖范围，最终结果需由医生结合测量和检查确认。",
        )

    def test_validate_baseline_omits_obesity_copy_below_adult_obesity_range(self):
        result = validate_baseline({
            "age": 32,
            "sex": "male",
            "height_cm": 170,
            "weight_kg": 80,
            "measured_at": "2026-08-18",
        })

        self.assertEqual(result["bmi"], 27.7)
        self.assertEqual(result["bmi_grade"], "超重")
        self.assertNotIn("diagnosis_copy", result)

    def test_validate_baseline_rejects_unsafe_or_inapplicable_measurements(self):
        cases = (
            ({"age": 17}, "仅支持18岁及以上成年人"),
            ({"age": 32, "sex": "other"}, "生理性别仅支持男或女"),
            ({"age": 32, "sex": "male", "height_cm": 99}, "身高需在100至250厘米之间"),
            ({"age": 32, "sex": "male", "height_cm": 170, "weight_kg": 19}, "体重需在20至500千克之间"),
            ({"age": 32, "sex": "male", "height_cm": 170, "weight_kg": 80, "waist_cm": 0, "measured_at": "2026-08-18"}, "腰围需为大于0的厘米数"),
            ({"age": 32, "sex": "male", "height_cm": 170, "weight_kg": 80, "hip_cm": -1, "measured_at": "2026-08-18"}, "臀围需为大于0的厘米数"),
            ({"age": 32, "sex": "male", "height_cm": 170, "weight_kg": 80}, "请补充最近一次测量时间"),
        )

        for payload, message in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, message):
                    validate_baseline(payload)


if __name__ == "__main__":
    unittest.main()
