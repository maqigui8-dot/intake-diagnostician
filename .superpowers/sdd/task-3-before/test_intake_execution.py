import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intake_execution import blank_field_states, calculate_execution, evaluate_threshold, merge_field_updates
from obesity_intake_schema import FIELD_DEFINITIONS


def confirmed_states(context=None):
    states = blank_field_states(context or {})
    for key, value in states.items():
        if value["status"] != "not_applicable":
            value.update({"status": "confirmed", "evidence": [f"{key} 已确认"], "confidence": 0.95})
    return states


class IntakeExecutionTests(unittest.TestCase):
    def test_blank_states_mark_condition_field_not_applicable(self):
        states = blank_field_states({"pregnancy_applicable": False})
        self.assertEqual(states["pregnancy"]["status"], "not_applicable")
        self.assertEqual(states["allergies"]["status"], "not_asked")

    def test_confirmed_and_partial_use_fixed_coefficients(self):
        states = blank_field_states({"pregnancy_applicable": False})
        states["main_goal"].update({"status": "confirmed", "evidence": ["希望减重"], "confidence": 0.96})
        states["height_weight"].update({"status": "partial", "evidence": ["体重约80公斤"], "confidence": 0.75})
        result = calculate_execution(states, {"pregnancy_applicable": False})
        self.assertEqual(result["raw_points"]["main_goal"], 4.0)
        self.assertEqual(result["raw_points"]["height_weight"], 2.5)

    def test_condition_field_is_removed_and_section_is_normalized(self):
        states = confirmed_states({"pregnancy_applicable": False})
        result = calculate_execution(states, {"pregnancy_applicable": False})
        self.assertEqual(result["differentiation_score"], 70.0)
        self.assertEqual(result["safety_score"], 30.0)
        self.assertEqual(result["total_score"], 100.0)

    def test_score_does_not_finish_when_hard_required_field_was_not_asked(self):
        states = confirmed_states({"pregnancy_applicable": False})
        states["allergies"].update({"status": "not_asked", "evidence": [], "confidence": 0.0})
        decision = evaluate_threshold(calculate_execution(states, {"pregnancy_applicable": False}), states, {"pregnancy_applicable": False})
        self.assertFalse(decision["can_complete"])
        self.assertIn("allergies", decision["blocking_keys"])

    def test_threshold_requires_all_three_scores(self):
        states = confirmed_states({"pregnancy_applicable": False})
        for item in FIELD_DEFINITIONS:
            if item.section == "differentiation" and item.key not in {"main_goal", "height_weight"}:
                states[item.key].update({"status": "not_asked", "evidence": [], "confidence": 0.0})
        decision = evaluate_threshold(calculate_execution(states, {"pregnancy_applicable": False}), states, {"pregnancy_applicable": False})
        self.assertFalse(decision["can_complete"])
        self.assertLess(decision["execution"]["differentiation_score"], 55)

    def test_merge_keeps_evidence_and_marks_conflict_partial(self):
        states = blank_field_states({})
        states = merge_field_updates(states, [{
            "field_key": "allergies", "status": "confirmed", "evidence": "没有过敏", "confidence": 0.95,
        }], source_turn=1)
        states = merge_field_updates(states, [{
            "field_key": "allergies", "status": "confirmed", "evidence": "青霉素过敏", "confidence": 0.92,
            "conflict": True,
        }], source_turn=2)
        self.assertEqual(states["allergies"]["status"], "partial")
        self.assertEqual(states["allergies"]["evidence"], ["没有过敏", "青霉素过敏"])
        self.assertEqual(len(states["allergies"]["conflicts"]), 1)


if __name__ == "__main__":
    unittest.main()
