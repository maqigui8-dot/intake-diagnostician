import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from obesity_intake_schema import FIELD_DEFINITIONS, get_applicable_fields, get_field_definition


class ObesityIntakeSchemaTests(unittest.TestCase):
    def test_registry_weights_are_70_and_30(self):
        differentiation = sum(item.weight for item in FIELD_DEFINITIONS if item.section == "differentiation")
        safety = sum(item.weight for item in FIELD_DEFINITIONS if item.section == "safety")
        self.assertEqual(differentiation, 70)
        self.assertEqual(safety, 30)

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


if __name__ == "__main__":
    unittest.main()
