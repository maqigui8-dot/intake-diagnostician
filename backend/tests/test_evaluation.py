import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.runner import evaluate_cases, load_cases
from evaluation.dialogues import build_dialogue_cases, evaluate_dialogues


class EvaluationTests(unittest.TestCase):
    def test_fixed_synthetic_set_has_unique_ids_and_required_categories(self):
        cases = load_cases()
        self.assertGreaterEqual(len(cases), 30)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        categories = {case["category"] for case in cases}
        self.assertTrue({"negation", "duration", "medication", "allergy", "red_flag", "ambiguous", "stop"} <= categories)
        self.assertTrue(all(case["synthetic"] is True for case in cases))

    def test_runner_reports_failures_without_hiding_them(self):
        summary = evaluate_cases([
            {"id": "red-positive", "synthetic": True, "category": "red_flag", "kind": "red_flag", "text": "最近有胸痛", "expected": ["胸痛"]},
            {"id": "red-negative", "synthetic": True, "category": "red_flag", "kind": "red_flag", "text": "最近有胸痛", "expected": []},
        ])
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed_ids"], ["red-negative"])
        self.assertEqual(summary["by_category"]["red_flag"]["passed"], 1)

    def test_fixed_set_runs_without_calling_a_remote_model(self):
        summary = evaluate_cases(load_cases())
        self.assertEqual(summary["total"], len(load_cases()))
        self.assertIn("failed_ids", summary)
        self.assertEqual(sum(item["total"] for item in summary["by_category"].values()), summary["total"])

    def test_dialogue_set_covers_30_fixed_multi_turn_scenarios(self):
        cases = build_dialogue_cases()
        self.assertEqual(len(cases), 30)
        self.assertEqual(len({item["id"] for item in cases}), 30)
        self.assertTrue(all(item["synthetic"] for item in cases))

    def test_dialogue_runner_reports_phase_rounds_and_safety_recall(self):
        summary = evaluate_dialogues(build_dialogue_cases())
        self.assertEqual(summary["total"], 30)
        self.assertEqual(summary["mode"], "offline_multi_turn_without_llm")
        self.assertEqual(len(summary["results"]), 30)
        self.assertTrue(all("rounds" in result and "phase" in result for result in summary["results"]))
        self.assertIn("red_flag_recall", summary)


if __name__ == "__main__":
    unittest.main()
