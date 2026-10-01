import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intake_execution import PATIENT_CORE_FIELD_KEYS, blank_field_states, calculate_execution
from intake_question_policy import decide_stop, is_clarification_request, select_next_field


class IntakeQuestionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.context = {"baseline_confirmed": True, "pregnancy_applicable": False}

    def test_red_flag_is_selected_before_symptom_gap(self):
        states = blank_field_states(self.context)
        self.assertEqual(select_next_field(states, [], self.context), "red_flags")

    def test_hard_safety_fields_precede_differentiation_fields(self):
        states = blank_field_states(self.context)
        states["red_flags"]["status"] = "confirmed"
        self.assertEqual(select_next_field(states, [], self.context), "allergies")

    def test_baseline_blocker_prevents_completion_even_when_other_fields_are_confirmed(self):
        context = {"baseline_confirmed": False, "pregnancy_applicable": False}
        states = blank_field_states(context)
        for value in states.values():
            if value["status"] != "not_applicable":
                value["status"] = "confirmed"

        result = decide_stop(states, calculate_execution(states, context), [], context)

        self.assertFalse(result["complete"])
        self.assertIn("baseline", result["blocking_keys"])

    def test_risk_gap_is_selected_before_tcm_gap_after_safety_is_complete(self):
        states = blank_field_states(self.context)
        for key in ("red_flags", "allergies", "medications", "important_history"):
            states[key]["status"] = "confirmed"

        next_key = select_next_field(states, [], self.context)

        self.assertEqual(next_key, "weight_change")

    def test_unknown_answer_retries_same_field_only_once(self):
        states = blank_field_states(self.context)
        states["red_flags"].update({"status": "partial", "attempts": 1})
        history = [{"question_key": "red_flags", "answer_quality": "unavailable", "attempt_number": 1}]
        self.assertEqual(select_next_field(states, history, self.context), "red_flags")
        history.append({"question_key": "red_flags", "answer_quality": "unavailable", "attempt_number": 2})
        states["red_flags"].update({"status": "unavailable", "attempts": 2})
        self.assertEqual(select_next_field(states, history, self.context), "allergies")

    def test_clarification_requests_are_detected_and_do_not_consume_attempts(self):
        states = blank_field_states(self.context)
        states["red_flags"]["status"] = "partial"
        history = [
            {"question_key": "red_flags", "answer_quality": "clarification"},
            {"question_key": "red_flags", "answer_quality": "clarification"},
        ]

        self.assertTrue(is_clarification_request("这是什么？"))
        self.assertTrue(is_clarification_request("我没听懂"))
        self.assertFalse(is_clarification_request("最近没有胸痛或呼吸困难"))
        self.assertEqual(select_next_field(states, history, self.context), "red_flags")

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

    def test_unresolved_conflict_is_reasked_before_stopping(self):
        states = blank_field_states(self.context)
        for value in states.values():
            if value["status"] != "not_applicable":
                value["status"] = "confirmed"
        states["appetite_thirst"]["conflicts"] = [{"turn": 1, "resolved": False}]

        result = decide_stop(states, calculate_execution(states, self.context), [], self.context)

        self.assertFalse(result["stop"])
        self.assertEqual(result["next_field_key"], "appetite_thirst")

    def test_all_confirmed_fields_are_reported_as_core_information_ready(self):
        states = blank_field_states(self.context)
        for value in states.values():
            if value["status"] != "not_applicable":
                value["status"] = "confirmed"
        result = decide_stop(states, calculate_execution(states, self.context), [], self.context, red_flags=[], ai_available=True)
        self.assertEqual(result["reason"], "core_information_ready")
        self.assertTrue(result["complete"])

    def test_core_information_ready_stops_without_chasing_optional_fields(self):
        states = blank_field_states(self.context)
        for key in PATIENT_CORE_FIELD_KEYS:
            if states[key]["status"] != "not_applicable":
                states[key]["status"] = "confirmed"
        context = {**self.context, "open_answer": "想改善体重"}

        result = decide_stop(states, calculate_execution(states, context), [], context)

        self.assertTrue(result["stop"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["reason"], "core_information_ready")


    def test_ai_unavailable_continues_all_collectable_fields(self):
        states = blank_field_states(self.context)
        for key in ("red_flags", "allergies", "medications", "important_history"):
            states[key]["status"] = "confirmed"
        result = decide_stop(states, calculate_execution(states, self.context), [], self.context, red_flags=[], ai_available=False)
        self.assertFalse(result["stop"])
        self.assertEqual(result["reason"], "continue_collecting")
        self.assertEqual(result["next_field_key"], "weight_change")


if __name__ == "__main__":
    unittest.main()
