import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intake_execution import (
    PATIENT_CORE_FIELD_KEYS,
    blank_field_states,
    calculate_execution,
    evaluate_patient_readiness,
    evaluate_threshold,
    merge_field_updates,
    migrate_field_states,
)
from obesity_intake_schema import FIELD_DEFINITIONS


def confirmed_states(context=None):
    states = blank_field_states(context or {})
    for key, value in states.items():
        if value["status"] != "not_applicable":
            value.update({"status": "confirmed", "evidence": [f"{key} 已确认"], "confidence": 0.95})
    return states


def reset_field(state):
    state.update({"status": "not_asked", "evidence": [], "confidence": 0.0, "conflicts": []})


class IntakeExecutionTests(unittest.TestCase):
    def test_patient_readiness_completes_with_core_fields_even_when_optional_details_are_unasked(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False, "open_answer": "想改善体重"}
        states = blank_field_states(context)
        for key in PATIENT_CORE_FIELD_KEYS:
            if states[key]["status"] != "not_applicable":
                states[key].update({"status": "confirmed", "evidence": ["已确认"]})

        readiness = evaluate_patient_readiness(states, context)

        self.assertTrue(readiness["can_complete"])
        self.assertEqual(readiness["blocking_keys"], [])
        self.assertIn("tongue", readiness["doctor_follow_up_keys"])

    def test_patient_readiness_requires_previsit_lifestyle_and_recent_tests(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False, "open_answer": "想改善体重"}
        states = blank_field_states(context)
        for key in PATIENT_CORE_FIELD_KEYS:
            if states[key]["status"] != "not_applicable":
                states[key].update({"status": "confirmed", "evidence": ["已确认"]})

        for key in ("diet_pattern", "exercise", "sleep_schedule", "glucose_tests"):
            states[key].update({"status": "not_asked", "evidence": []})

        readiness = evaluate_patient_readiness(states, context)

        self.assertFalse(readiness["can_complete"])
        self.assertEqual(
            set(readiness["blocking_keys"]),
            {"diet_pattern", "exercise", "sleep_schedule", "glucose_tests"},
        )

    def test_patient_readiness_keeps_unconfirmed_core_safety_field_as_blocker(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False, "open_answer": "想改善体重"}
        states = blank_field_states(context)
        for key in PATIENT_CORE_FIELD_KEYS:
            if states[key]["status"] != "not_applicable":
                states[key].update({"status": "confirmed", "evidence": ["已确认"]})
        states["allergies"].update({"status": "not_asked", "evidence": []})

        readiness = evaluate_patient_readiness(states, context)

        self.assertFalse(readiness["can_complete"])
        self.assertIn("allergies", readiness["blocking_keys"])

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
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        result = calculate_execution(states, context)
        self.assertTrue(result["baseline_ready"])
        self.assertEqual(result["risk_score"], 100.0)
        self.assertEqual(result["tcm_score"], 100.0)
        self.assertEqual(result["safety_score"], 100.0)
        self.assertEqual(result["differentiation_score"], 70.0)
        self.assertEqual(result["total_score"], 100.0)

    def test_score_does_not_finish_when_hard_required_field_was_not_asked(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        states["allergies"].update({"status": "not_asked", "evidence": [], "confidence": 0.0})
        decision = evaluate_threshold(calculate_execution(states, context), states, context)
        self.assertFalse(decision["can_complete"])
        self.assertIn("allergies", decision["blocking_keys"])

    def test_high_optional_score_cannot_bypass_missing_baseline(self):
        states = confirmed_states({"pregnancy_applicable": False})
        execution = calculate_execution(states, {"pregnancy_applicable": False})
        result = evaluate_threshold(execution, states, {"pregnancy_applicable": False})

        self.assertFalse(result["can_complete"])
        self.assertIn("baseline", result["blocking_keys"])

    def test_all_layers_must_reach_their_thresholds(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        complete_states = confirmed_states(context)
        scenarios = [(complete_states, True)]
        for layer in ("risk", "tcm", "safety"):
            states = confirmed_states(context)
            for item in FIELD_DEFINITIONS:
                if item.layer == layer:
                    reset_field(states[item.key])
            scenarios.append((states, False))

        for states, expected in scenarios:
            execution = calculate_execution(states, context)
            decision = evaluate_threshold(execution, states, context)
            threshold_result = (
                execution["baseline_ready"]
                and execution["risk_score"] >= 80
                and execution["tcm_score"] >= 70
                and execution["safety_score"] >= 100
            )
            self.assertEqual(decision["can_complete"], expected)
            self.assertEqual(decision["can_complete"], threshold_result)

    def test_legacy_total_score_is_not_a_completion_gate(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        execution = calculate_execution(states, context)
        execution["total_score"] = 0.0

        self.assertTrue(evaluate_threshold(execution, states, context)["can_complete"])

    def test_unresolved_conflict_is_an_explicit_blocker(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        states["main_goal"]["conflicts"] = [{"turn": 2, "evidence": "相互矛盾"}]

        decision = evaluate_threshold(calculate_execution(states, context), states, context)

        self.assertFalse(decision["can_complete"])
        self.assertIn("main_goal", decision["blocking_keys"])

    def test_optional_unavailable_tcm_fields_leave_denominator_after_final_retry(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        for key in ("edema_heaviness", "chest_abdomen", "tongue"):
            states[key].update({"status": "unavailable", "attempts": 2})

        execution = calculate_execution(states, context)

        self.assertEqual(execution["layer_max"]["tcm"], 26.0)
        self.assertEqual(execution["tcm_score"], 100.0)
        self.assertTrue(evaluate_threshold(execution, states, context)["can_complete"])

    def test_optional_unavailable_field_stays_in_denominator_before_final_retry(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        states["tongue"].update({"status": "unavailable", "attempts": 1})

        execution = calculate_execution(states, context)

        self.assertEqual(execution["layer_max"]["tcm"], 40.0)
        self.assertLess(execution["tcm_score"], 100.0)

    def test_fully_retried_optional_only_layer_with_zero_denominator_is_complete(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        for item in FIELD_DEFINITIONS:
            if item.layer == "tcm":
                states[item.key].update({"status": "unavailable", "attempts": item.max_attempts})

        execution = calculate_execution(states, context)

        self.assertEqual(execution["layer_max"]["tcm"], 0.0)
        self.assertEqual(execution["tcm_score"], 100.0)
        self.assertTrue(evaluate_threshold(execution, states, context)["can_complete"])

    def test_required_unavailable_field_remains_denominator_and_blocker(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        states["allergies"].update({"status": "unavailable", "attempts": 2})

        execution = calculate_execution(states, context)
        decision = evaluate_threshold(execution, states, context)

        self.assertEqual(execution["layer_max"]["safety"], 22.0)
        self.assertLess(execution["safety_score"], 100.0)
        self.assertIn("allergies", decision["blocking_keys"])

    def test_legacy_metabolic_state_is_preserved_without_confirming_new_groups(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        test_keys = {
            "glucose_tests", "lipid_tests", "uric_acid_test",
            "liver_tests", "kidney_tests", "thyroid_tests",
        }
        for key in test_keys:
            states.pop(key)
        states["metabolic_tests"] = {
            "status": "confirmed", "evidence": ["近期代谢检查已确认"], "confidence": 0.9,
            "attempts": 1, "conflicts": [], "audit": [],
        }

        migrated = migrate_field_states(states, context)
        execution = calculate_execution(migrated, context)

        self.assertEqual(migrated["metabolic_tests"]["evidence"], ["近期代谢检查已确认"])
        for key in test_keys:
            self.assertEqual(migrated[key]["status"], "not_asked")
            self.assertEqual(migrated[key]["evidence"], [])
            self.assertEqual(execution["raw_points"][key], 0.0)

    def test_migration_without_context_preserves_not_applicable_fields(self):
        states = blank_field_states({"pregnancy_applicable": False})

        migrated = migrate_field_states(states)

        self.assertEqual(migrated["pregnancy"]["status"], "not_applicable")

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

    def test_later_confirmed_update_resolves_conflict_without_erasing_history(self):
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = confirmed_states(context)
        states = merge_field_updates(states, [{
            "field_key": "main_goal", "status": "confirmed", "evidence": "目标表述矛盾",
            "confidence": 0.8, "conflict": True,
        }], source_turn=2)

        unresolved = evaluate_threshold(calculate_execution(states, context), states, context)
        self.assertIn("main_goal", unresolved["blocking_keys"])

        states = merge_field_updates(states, [{
            "field_key": "main_goal", "status": "confirmed", "evidence": "明确希望减重",
            "confidence": 0.98,
        }], source_turn=3)
        resolved = evaluate_threshold(calculate_execution(states, context), states, context)

        self.assertNotIn("main_goal", resolved["blocking_keys"])
        self.assertTrue(resolved["can_complete"])
        self.assertEqual(len(states["main_goal"]["conflicts"]), 1)
        self.assertTrue(states["main_goal"]["conflicts"][0]["resolved"])
        self.assertEqual(states["main_goal"]["conflicts"][0]["resolved_turn"], 3)

    def test_pregnancy_reactivation_preserves_history_and_becomes_partial(self):
        states = blank_field_states({"pregnancy_applicable": False})
        pregnancy = states["pregnancy"]
        pregnancy.update({
            "evidence": ["历史备孕信息"],
            "attempts": 1,
            "conflicts": [{"turn": 1, "evidence": "历史信息待核实"}],
            "audit": [{"turn": 1, "from_status": "not_asked", "to_status": "partial"}],
        })

        migrated = migrate_field_states(states, {"pregnancy_applicable": True})

        self.assertEqual(migrated["pregnancy"]["status"], "partial")
        self.assertEqual(migrated["pregnancy"]["evidence"], ["历史备孕信息"])
        self.assertEqual(migrated["pregnancy"]["attempts"], 1)
        self.assertEqual(migrated["pregnancy"]["conflicts"], [{"turn": 1, "evidence": "历史信息待核实"}])
        self.assertEqual(len(migrated["pregnancy"]["audit"]), 1)


if __name__ == "__main__":
    unittest.main()
