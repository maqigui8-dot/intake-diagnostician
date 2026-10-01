import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from obesity_intake_schema import FIELD_DEFINITIONS, get_applicable_fields, get_field_definition


class ObesityIntakeSchemaTests(unittest.TestCase):
    def test_registry_has_guideline_fields_with_layer_and_source(self):
        required_keys = {
            "childhood_obesity",
            "family_history",
            "smoking",
            "alcohol",
            "work_activity",
            "binge_eating",
            "glucose_tests",
            "lipid_tests",
            "uric_acid_test",
            "liver_tests",
            "kidney_tests",
            "thyroid_tests",
        }
        definitions = {item.key: item for item in FIELD_DEFINITIONS}

        self.assertTrue(required_keys <= definitions.keys())
        self.assertTrue(all(item.layer in {"baseline", "risk", "tcm", "safety"} for item in FIELD_DEFINITIONS))
        self.assertTrue(all(item.source.strip() for item in FIELD_DEFINITIONS))

    def test_metabolic_tests_is_split_into_structured_groups(self):
        keys = {item.key for item in FIELD_DEFINITIONS}
        self.assertNotIn("metabolic_tests", keys)

    def test_layer_weights_are_positive_and_each_scored_layer_has_fields(self):
        for layer in ("risk", "tcm", "safety"):
            weights = [item.weight for item in FIELD_DEFINITIONS if item.layer == layer]
            self.assertTrue(weights, layer)
            self.assertTrue(all(weight > 0 for weight in weights), layer)

    def test_field_keys_are_unique_and_questions_are_complete(self):
        keys = [item.key for item in FIELD_DEFINITIONS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(item.question.strip() for item in FIELD_DEFINITIONS))
        self.assertTrue(all(item.retry_question.strip() for item in FIELD_DEFINITIONS))

    def test_prescription_safety_hard_required_fields_are_fixed(self):
        hard_keys = {item.key for item in FIELD_DEFINITIONS if item.hard_required}
        self.assertEqual(hard_keys, {"allergies", "medications", "important_history", "red_flags"})

    def test_pregnancy_field_is_removed_when_not_applicable(self):
        applicable = {item.key for item in get_applicable_fields({"pregnancy_applicable": False})}
        self.assertNotIn("pregnancy", applicable)
        self.assertIn("allergies", applicable)

    def test_field_lookup_rejects_unknown_key(self):
        self.assertEqual(get_field_definition("allergies").weight, 6)
        with self.assertRaises(KeyError):
            get_field_definition("unknown_field")

    def test_section_is_retained_for_compatibility(self):
        for item in FIELD_DEFINITIONS:
            if item.layer in {"baseline", "risk", "tcm"}:
                self.assertEqual(item.section, "differentiation")
            else:
                self.assertEqual(item.section, "safety")

    def test_tongue_is_optional_and_pulse_is_not_an_online_field(self):
        self.assertFalse(get_field_definition("tongue").hard_required)
        self.assertNotIn("pulse", {item.key for item in FIELD_DEFINITIONS})


if __name__ == "__main__":
    unittest.main()
