import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intake_flow import (
    OPEN_QUESTION,
    apply_analysis_turn,
    generate_report,
    get_intake_state,
    intake_sessions,
    submit_follow_up_answer,
    submit_open_answer,
)


class IntakeFlowTests(unittest.TestCase):
    def setUp(self):
        intake_sessions.clear()

    def test_new_session_starts_with_open_question(self):
        state = get_intake_state("session-a")
        self.assertEqual(state["phase"], "open_intake")
        self.assertEqual(state["open_question"], OPEN_QUESTION)
        self.assertEqual(state["follow_up_count"], 0)
        self.assertFalse(state["is_complete"])

    def test_open_answer_is_preserved_as_patient_evidence(self):
        state = submit_open_answer("session-a", "体重这半年涨了十斤，饭后容易困")
        self.assertEqual(state["open_answer"], "体重这半年涨了十斤，饭后容易困")
        self.assertEqual(state["latest_answer"], "体重这半年涨了十斤，饭后容易困")
        self.assertEqual(state["phase"], "processing")
        self.assertEqual(state["turn"], 1)

    def test_open_answer_rejects_blank_content(self):
        with self.assertRaisesRegex(ValueError, "开放回答不能为空"):
            submit_open_answer("session-a", "   ")

    def test_follow_up_uses_server_side_current_question(self):
        session = intake_sessions.get("session-a")
        session.update({
            "phase": "follow_up",
            "current_question": "您有药物过敏吗？",
            "current_field_key": "allergies",
            "attempt_number": 1,
        })
        state = submit_follow_up_answer("session-a", "没有")
        self.assertEqual(state["follow_up_answers"][0]["question_key"], "allergies")
        self.assertEqual(state["follow_up_answers"][0]["answer"], "没有")
        self.assertEqual(state["phase"], "processing")

    def test_detailed_answer_is_provided_when_only_one_optional_item_is_unavailable(self):
        session = intake_sessions.get("session-a")
        session.update({
            "phase": "follow_up",
            "current_question": "您有药物过敏吗？",
            "current_field_key": "allergies",
            "attempt_number": 1,
        })

        state = submit_follow_up_answer(
            "session-a",
            "没有药物过敏，身高165厘米，体重85公斤，现在不方便提供舌照。",
        )

        self.assertEqual(state["follow_up_answers"][0]["answer_quality"], "provided")

    def test_unknown_answer_marks_field_unavailable_after_second_attempt(self):
        session = intake_sessions.get("session-a")
        for attempt in (1, 2):
            session.update({
                "phase": "follow_up",
                "current_question": "您有明确过敏吗？",
                "current_field_key": "allergies",
                "attempt_number": attempt,
            })
            state = submit_follow_up_answer("session-a", "不知道")
        self.assertEqual(state["field_states"]["allergies"]["status"], "unavailable")
        self.assertEqual(state["field_states"]["allergies"]["attempts"], 2)

    def test_thirteenth_follow_up_answer_is_preserved(self):
        session = intake_sessions.get("session-a")
        session["follow_up_answers"] = [
            {
                "question": f"历史问题 {index}",
                "answer": f"历史回答 {index}",
                "question_key": f"history_{index}",
                "attempt_number": 1,
                "answer_quality": "provided",
            }
            for index in range(12)
        ]
        session.update({
            "phase": "follow_up",
            "current_question": "最近有没有胸痛或呼吸困难？",
            "current_field_key": "red_flags",
            "attempt_number": 1,
        })

        state = submit_follow_up_answer("session-a", "没有")

        self.assertEqual(len(state["follow_up_answers"]), 13)
        self.assertEqual(state["follow_up_answers"][-1]["question_key"], "red_flags")

    def test_analysis_turn_updates_execution_and_next_question(self):
        submit_open_answer("session-a", "想减重，半年胖了十斤")
        state = apply_analysis_turn(
            "session-a",
            extraction={
                "field_updates": [
                    {"field_key": "main_goal", "status": "confirmed", "evidence": "想减重", "confidence": 0.98},
                    {"field_key": "weight_change", "status": "confirmed", "evidence": "半年胖了十斤", "confidence": 0.95},
                ],
                "conflicts": [],
                "red_flags": [],
            },
            decision={"stop": False, "complete": False, "reason": "continue_collecting", "next_field_key": "red_flags", "blocking_keys": []},
            question="最近有没有胸痛、明显呼吸困难或晕厥？",
            attempt_number=1,
        )
        self.assertEqual(state["phase"], "follow_up")
        self.assertEqual(state["current_field_key"], "red_flags")
        self.assertGreater(state["execution"]["total_score"], 0)

    def test_red_flag_alert_is_preserved_while_questioning_continues(self):
        submit_open_answer("session-a", "最近出现过胸痛，也想控制体重")
        state = apply_analysis_turn(
            "session-a",
            extraction={
                "field_updates": [
                    {"field_key": "red_flags", "status": "confirmed", "evidence": "胸痛", "confidence": 0.98},
                ],
                "conflicts": [],
                "red_flags": ["胸痛"],
            },
            decision={"stop": False, "complete": False, "reason": "continue_collecting", "next_field_key": "allergies", "blocking_keys": []},
            question="您有明确的药物或食物过敏吗？",
            attempt_number=1,
        )

        self.assertEqual(state["phase"], "follow_up")
        self.assertEqual(state["safety_alerts"], ["胸痛"])
        self.assertIsNone(state["report_markdown"])

    def test_stopped_turn_generates_report_and_reason(self):
        submit_open_answer("session-a", "想减重")
        state = apply_analysis_turn(
            "session-a",
            extraction={"field_updates": [], "conflicts": [], "red_flags": []},
            decision={"stop": True, "complete": False, "reason": "no_collectable_gap", "next_field_key": None, "blocking_keys": []},
            question="",
            attempt_number=0,
        )
        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["stop_reason"], "no_collectable_gap")
        self.assertIn("诊前资料", state["report_markdown"])

    def test_report_contains_open_answer_and_no_diagnosis_or_prescription(self):
        state = get_intake_state("session-a")
        state["open_answer"] = "最近半年体重增加，想改善疲乏"
        report = generate_report(state)
        self.assertIn("最近半年体重增加", report)
        self.assertIn("待诊中确认", report)
        self.assertNotIn("main_goal", report)
        self.assertNotIn("处方：", report)
        self.assertNotIn("证型：", report)


if __name__ == "__main__":
    unittest.main()
