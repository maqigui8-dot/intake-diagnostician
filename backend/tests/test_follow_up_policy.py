import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from follow_up_policy import apply_follow_up_policy


def analysis(**overrides):
    value = {
        "status": "completed",
        "completeness_status": "needs_follow_up",
        "completeness_summary": "仍缺少一项关键信息",
        "missing_required_items": ["症状发生时间"],
        "optional_items": [],
        "follow_up_key": "symptom_timing",
        "follow_up_kind": "required",
        "follow_up_questions": ["不舒服通常在什么时候更明显？"],
        "safety_alerts": [],
        "recommended_exams": [],
    }
    value.update(overrides)
    return value


class FollowUpPolicyTests(unittest.TestCase):
    def test_new_required_gap_can_continue(self):
        result = apply_follow_up_policy(analysis(), {"follow_up_answers": [], "follow_up_count": 6})
        self.assertEqual(result["follow_up_questions"], ["不舒服通常在什么时候更明显？"])

    def test_optional_gap_cannot_block_completion(self):
        result = apply_follow_up_policy(
            analysis(follow_up_key="old_exam", follow_up_kind="optional"),
            {"follow_up_answers": [], "follow_up_count": 2},
        )
        self.assertEqual(result["completeness_status"], "complete")
        self.assertEqual(result["follow_up_questions"], [])
        self.assertEqual(result["completion_reason"], "optional_only")

    def test_attempted_gap_cannot_be_asked_again(self):
        state = {
            "follow_up_count": 1,
            "follow_up_answers": [
                {"question_key": "symptom_timing", "question": "什么时候明显？", "answer": "不知道"}
            ],
        }
        result = apply_follow_up_policy(analysis(), state)
        self.assertEqual(result["follow_up_questions"], [])
        self.assertEqual(result["completion_reason"], "duplicate_gap")

    def test_more_than_twelve_answers_do_not_block_a_new_required_gap(self):
        state = {
            "follow_up_count": 12,
            "follow_up_answers": [
                {"question_key": f"gap_{index}", "question": f"问题 {index}", "answer": "回答"}
                for index in range(12)
            ],
        }
        result = apply_follow_up_policy(analysis(follow_up_key="new_gap"), state)
        self.assertEqual(result["follow_up_questions"], ["不舒服通常在什么时候更明显？"])
        self.assertEqual(result["completion_reason"], "continue_required_gap")


if __name__ == "__main__":
    unittest.main()
