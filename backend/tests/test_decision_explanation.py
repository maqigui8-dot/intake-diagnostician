import unittest

from decision_explanation import build_decision_explanation
from intake_execution import PATIENT_CORE_FIELD_KEYS, blank_field_states


class DecisionExplanationTests(unittest.TestCase):
    def test_ready_core_can_coexist_with_optional_gaps(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        fields = blank_field_states(context)
        for key in PATIENT_CORE_FIELD_KEYS:
            if fields[key]["status"] != "not_applicable":
                fields[key]["status"] = "confirmed"

        explanation = build_decision_explanation({
            "phase": "completed", "stop_reason": "core_information_ready",
            "context": context, "field_states": fields,
        })
        readiness = explanation["readiness"]

        self.assertEqual(readiness["status"], "ready")
        self.assertEqual(readiness["core"], {"completed": 16, "total": 16})
        self.assertEqual(readiness["safety"], {"completed": 4, "total": 4})
        self.assertEqual(readiness["core_conflicts"], 0)
        self.assertIn("tongue", readiness["optional_keys"])
        self.assertEqual(readiness["blocking_keys"], [])

    def test_unresolved_core_conflict_blocks_ready_status(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": True}
        fields = blank_field_states(context)
        for key in PATIENT_CORE_FIELD_KEYS:
            fields[key]["status"] = "confirmed"
        fields["medications"]["conflicts"] = [{"evidence": "用药前后说法不同", "resolved": False}]

        readiness = build_decision_explanation({
            "phase": "follow_up", "context": context, "field_states": fields,
        })["readiness"]

        self.assertEqual(readiness["status"], "collecting")
        self.assertEqual(readiness["core"], {"completed": 16, "total": 17})
        self.assertEqual(readiness["safety"], {"completed": 4, "total": 5})
        self.assertEqual(readiness["core_conflicts"], 1)
        self.assertEqual(readiness["blocking_keys"], ["medications"])

    def test_protective_end_is_not_reported_as_ready(self):
        explanation = build_decision_explanation({
            "phase": "incomplete", "stop_reason": "patient_unavailable",
            "context": {"baseline_confirmed": True, "pregnancy_applicable": False},
            "field_states": blank_field_states({"baseline_confirmed": True, "pregnancy_applicable": False}),
        })

        self.assertEqual(explanation["readiness"]["status"], "needs_doctor")
        self.assertTrue(explanation["stop"]["should_stop"])

    def test_escalated_end_is_prioritized_over_core_readiness(self):
        explanation = build_decision_explanation({
            "phase": "escalated", "stop_reason": "red_flag_escalation",
            "context": {"baseline_confirmed": False, "pregnancy_applicable": False},
            "field_states": blank_field_states({"baseline_confirmed": False, "pregnancy_applicable": False}),
        })

        self.assertEqual(explanation["readiness"]["status"], "escalated")
        self.assertFalse(explanation["readiness"]["baseline_ready"])
        self.assertIn("baseline", explanation["readiness"]["blocking_keys"])

    def test_continuing_state_explains_selected_field(self):
        fields = blank_field_states({"baseline_confirmed": True, "pregnancy_applicable": True})
        state = {
            "phase": "follow_up",
            "context": {"baseline_confirmed": True, "pregnancy_applicable": True},
            "field_states": fields,
            "current_field_key": "main_goal",
            "attempt_number": 1,
            "blocking_keys": ["main_goal"],
            "audit": [{"event": "question_selected", "field_key": "main_goal"}],
        }

        explanation = build_decision_explanation(state)

        self.assertEqual(explanation["status"], "continue")
        self.assertEqual(explanation["selected_field"]["key"], "main_goal")
        self.assertGreater(explanation["core_total"], explanation["core_completed"])
        self.assertFalse(explanation["stop"]["should_stop"])

    def test_terminal_state_explains_stop_and_timeline(self):
        state = {
            "phase": "completed",
            "context": {"baseline_confirmed": True, "pregnancy_applicable": False},
            "field_states": {},
            "stop_reason": "core_information_ready",
            "audit": [{"event": "session_completed", "turn": 5}],
        }

        explanation = build_decision_explanation(state)

        self.assertTrue(explanation["stop"]["should_stop"])
        self.assertTrue(explanation["stop"]["reason"])
        self.assertIsInstance(explanation["timeline"], list)


if __name__ == "__main__":
    unittest.main()
