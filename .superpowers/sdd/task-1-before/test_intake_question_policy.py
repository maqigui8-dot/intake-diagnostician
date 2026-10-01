import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intake_execution import blank_field_states, calculate_execution
from intake_question_policy import decide_stop, select_next_field


class IntakeQuestionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.context = {"pregnancy_applicable": False}

    def test_red_flag_is_selected_before_symptom_gap(self):
        states = blank_field_states(self.context)
        self.assertEqual(select_next_field(states, [], self.context), "red_flags")

    def test_hard_safety_fields_precede_differentiation_fields(self):
        states = blank_field_states(self.context)
        states["red_flags"]["status"] = "confirmed"
        self.assertEqual(select_next_field(states, [], self.context), "allergies")

    def test_unknown_answer_retries_same_field_only_once(self):
        states = blank_field_states(self.context)
        states["red_flags"].update({"status": "partial", "attempts": 1})
        history = [{"question_key": "red_flags", "answer_quality": "unavailable", "attempt_number": 1}]
        self.assertEqual(select_next_field(states, history, self.context), "red_flags")
        history.append({"question_key": "red_flags", "answer_quality": "unavailable", "attempt_number": 2})
        states["red_flags"].update({"status": "unavailable", "attempts": 2})
        self.assertEqual(select_next_field(states, history, self.context), "allergies")

    def test_red_flag_keeps_collecting_with_a_persistent_alert(self):
        states = blank_field_states(self.context)
        result = decide_stop(states, calculate_execution(states, self.context), [], self.context, red_flags=["胸痛"], ai_available=True)
        self.assertFalse(result["stop"])
        self.assertEqual(result["reason"], "continue_collecting")
        self.assertEqual(result["next_field_key"], "red_flags")

    def test_more_than_twelve_rounds_continue_when_a_field_is_collectable(self):
        states = blank_field_states(self.context)
        history = [{"question_key": f"gap_{index}"} for index in range(12)]
        result = decide_stop(states, calculate_execution(states, self.context), history, self.context, red_flags=[], ai_available=True)
        self.assertFalse(result["stop"])
        self.assertEqual(result["reason"], "continue_collecting")
        self.assertEqual(result["next_field_key"], "red_flags")

    def test_threshold_reached_is_normal_completion(self):
        states = blank_field_states(self.context)
        for value in states.values():
            if value["status"] != "not_applicable":
                value["status"] = "confirmed"
        result = decide_stop(states, calculate_execution(states, self.context), [], self.context, red_flags=[], ai_available=True)
        self.assertEqual(result["reason"], "threshold_reached")
        self.assertTrue(result["complete"])

    def test_ai_fallback_stops_after_fixed_safety_fields(self):
        states = blank_field_states(self.context)
        for key in ("red_flags", "allergies", "medications", "important_history"):
            states[key]["status"] = "confirmed"
        result = decide_stop(states, calculate_execution(states, self.context), [], self.context, red_flags=[], ai_available=False)
        self.assertEqual(result["reason"], "ai_unavailable")


if __name__ == "__main__":
    unittest.main()
