import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intake_execution import PATIENT_CORE_FIELD_KEYS
from intake_flow import (
    OPEN_QUESTION,
    apply_analysis_turn,
    complete_intake_session,
    generate_report,
    get_intake_state,
    intake_sessions,
    set_baseline,
    submit_follow_up_answer,
    submit_open_answer,
)
import main
from main import BaselineRequest, submit_baseline


class IntakeFlowTests(unittest.TestCase):
    def setUp(self):
        intake_sessions.clear()

    def _confirm_baseline(self, session_id: str = "session-a"):
        return set_baseline(session_id, {
            "age": 32,
            "sex": "female",
            "height_cm": 170,
            "weight_kg": 81,
            "measured_at": "2026-08-18",
        })

    def test_new_session_starts_in_explicit_baseline_collection_phase(self):
        state = get_intake_state("session-a")
        self.assertEqual(state["phase"], "baseline_collection")
        self.assertEqual(state["open_question"], OPEN_QUESTION)
        self.assertEqual(state["follow_up_count"], 0)
        self.assertFalse(state["is_complete"])
        self.assertIsNone(state["baseline"])
        self.assertIsNone(state["bmi_assessment"])
        self.assertFalse(state["baseline_confirmed"])
        self.assertFalse(state["context"]["baseline_confirmed"])

    def test_baseline_is_normalized_and_confirmed_before_open_intake(self):
        state = set_baseline("session-a", {
            "age": 32,
            "sex": "female",
            "height_cm": 170,
            "weight_kg": 81,
            "waist_cm": 85,
            "hip_cm": 100,
            "measured_at": "2026-08-18",
        })

        self.assertEqual(state["phase"], "open_intake")
        self.assertTrue(state["baseline_confirmed"])
        self.assertTrue(state["context"]["baseline_confirmed"])
        self.assertEqual(state["baseline"], {
            "age": 32,
            "sex": "female",
            "height_cm": 170.0,
            "weight_kg": 81.0,
            "waist_cm": 85.0,
            "hip_cm": 100.0,
            "measured_at": "2026-08-18",
        })
        self.assertEqual(state["bmi_assessment"]["bmi"], 28.0)
        self.assertEqual(state["bmi_assessment"]["bmi_grade"], "轻度肥胖范围")
        self.assertEqual(
            state["bmi_assessment"]["diagnosis_copy"],
            "当前BMI达到成人肥胖范围，最终结果需由医生结合测量和检查确认。",
        )
        open_state = submit_open_answer("session-a", "体重这半年涨了十斤，饭后容易困")
        self.assertEqual(open_state["phase"], "processing")

    def test_open_answer_requires_confirmed_baseline(self):
        with self.assertRaisesRegex(ValueError, "请先完成基础测量"):
            submit_open_answer("session-a", "想减重")

        state = get_intake_state("session-a")
        self.assertEqual(state["phase"], "baseline_collection")
        self.assertEqual(state["open_answer"], "")
        self.assertIsNone(state["report_markdown"])

    def test_manual_completion_requires_confirmed_baseline(self):
        with self.assertRaisesRegex(ValueError, "请先完成基础测量"):
            complete_intake_session("session-a")

        state = get_intake_state("session-a")
        self.assertEqual(state["phase"], "baseline_collection")
        self.assertIsNone(state["report_markdown"])

    def test_manual_completion_below_threshold_is_protective_incomplete(self):
        self._confirm_baseline()

        state = complete_intake_session("session-a")

        self.assertEqual(state["phase"], "incomplete")
        self.assertFalse(state["is_complete"])
        self.assertEqual(state["stop_reason"], "manual_incomplete")
        self.assertTrue(state["blocking_keys"])
        self.assertIn("诊前资料", state["report_markdown"])

    def test_manual_completion_succeeds_only_after_threshold(self):
        self._confirm_baseline()
        session = intake_sessions.get("session-a")
        for field in session["field_states"].values():
            if field["status"] != "not_applicable":
                field["status"] = "confirmed"

        state = complete_intake_session("session-a")

        self.assertEqual(state["phase"], "completed")
        self.assertTrue(state["is_complete"])
        self.assertEqual(state["stop_reason"], "manual_completion")

    def test_manual_completion_succeeds_when_core_information_is_ready(self):
        self._confirm_baseline()
        session = intake_sessions.get("session-a")
        session["open_answer"] = "想改善体重"
        for key in PATIENT_CORE_FIELD_KEYS:
            if session["field_states"][key]["status"] != "not_applicable":
                session["field_states"][key]["status"] = "confirmed"

        state = complete_intake_session("session-a")

        self.assertEqual(state["phase"], "completed")
        self.assertTrue(state["is_complete"])

    def test_analyze_endpoint_requires_confirmed_baseline(self):
        async def submit_unbaselined_analysis():
            with patch.object(main, "get_analysis_agent", return_value=object()), patch.object(main, "process_intake_turn") as process:
                with self.assertRaises(main.HTTPException) as error:
                    await main.analyze_structured_intake("session-a")
                self.assertEqual(error.exception.status_code, 400)
                self.assertIn("请先完成基础测量", error.exception.detail)
                process.assert_not_called()

        asyncio.run(submit_unbaselined_analysis())

    def test_manual_completion_endpoint_requires_confirmed_baseline(self):
        async def complete_unbaselined_session():
            with self.assertRaises(main.HTTPException) as error:
                await main.complete_structured_intake("session-a")
            self.assertEqual(error.exception.status_code, 400)
            self.assertIn("请先完成基础测量", error.exception.detail)

        asyncio.run(complete_unbaselined_session())

    def test_analyze_timeout_falls_back_to_deterministic_next_field(self):
        self._confirm_baseline()
        submit_open_answer("session-a", "最近半年胖了10斤")
        session = intake_sessions.get("session-a")
        session["field_states"]["red_flags"].update({
            "status": "confirmed", "evidence": ["没有"], "confidence": 1.0,
        })

        real_process = main.process_intake_turn
        calls = []

        def fake_process(session_id, agent):
            calls.append(agent)
            if len(calls) == 1:
                raise TimeoutError()
            return real_process(session_id, agent)

        async def timeout_analyze():
            with patch.object(main, "process_intake_turn", side_effect=fake_process):
                return await main.analyze_structured_intake("session-a")

        asyncio.run(timeout_analyze())

        self.assertEqual(len(calls), 2)
        internal = intake_sessions.get("session-a")
        self.assertEqual(internal["phase"], "follow_up")
        self.assertEqual(internal["current_field_key"], "allergies")
        self.assertNotEqual(internal["current_field_key"], "red_flags")

    def test_baseline_endpoint_stores_the_measurement(self):
        response = asyncio.run(submit_baseline(
            "session-a",
            BaselineRequest(
                age=32,
                sex="male",
                height_cm=170,
                weight_kg=80,
                measured_at="2026-08-18",
            ),
        ))

        self.assertEqual(response["phase"], "open_intake")
        state = get_intake_state("session-a")
        self.assertTrue(state["baseline_confirmed"])
        self.assertEqual(state["bmi_assessment"]["bmi"], 27.7)

    def test_open_answer_is_preserved_as_patient_evidence(self):
        self._confirm_baseline()
        state = submit_open_answer("session-a", "体重这半年涨了十斤，饭后容易困")
        self.assertEqual(state["open_answer"], "体重这半年涨了十斤，饭后容易困")
        self.assertEqual(state["latest_answer"], "体重这半年涨了十斤，饭后容易困")
        self.assertEqual(state["phase"], "processing")
        self.assertEqual(state["turn"], 1)

    def test_open_answer_rejects_blank_content(self):
        self._confirm_baseline()
        with self.assertRaisesRegex(ValueError, "开放回答不能为空"):
            submit_open_answer("session-a", "   ")

    def test_follow_up_uses_server_side_current_question(self):
        self._confirm_baseline()
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
        self._confirm_baseline()
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

    def test_clarification_does_not_consume_attempt_or_update_field(self):
        self._confirm_baseline("clarify")
        session = intake_sessions.get("clarify")
        session.update({
            "phase": "follow_up",
            "current_question": "您有明确的药物或食物过敏吗？",
            "current_field_key": "allergies",
            "attempt_number": 1,
        })

        state = submit_follow_up_answer("clarify", "这是什么意思？")

        self.assertEqual(state["follow_up_answers"][-1]["answer_quality"], "clarification")
        self.assertEqual(state["field_states"]["allergies"]["attempts"], 0)

    def test_unknown_answer_marks_field_unavailable_after_second_attempt(self):
        self._confirm_baseline()
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
        self._confirm_baseline()
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
        self._confirm_baseline()
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
        self._confirm_baseline()
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

    def test_incomplete_stop_reasons_never_mark_session_complete(self):
        for reason in ("patient_unavailable", "duplicate_gap", "no_collectable_gap", "ai_unavailable"):
            with self.subTest(reason=reason):
                session_id = f"stop-{reason}"
                self._confirm_baseline(session_id)
                submit_open_answer(session_id, "想减重")
                state = apply_analysis_turn(
                    session_id,
                    extraction={"field_updates": [], "conflicts": [], "red_flags": []},
                    decision={"stop": True, "complete": False, "reason": reason, "next_field_key": None, "blocking_keys": []},
                    question="",
                    attempt_number=0,
                )

                self.assertEqual(state["phase"], "incomplete")
                self.assertFalse(state["is_complete"])
                self.assertEqual(state["stop_reason"], reason)
                self.assertTrue(state["blocking_keys"])
                self.assertIn("诊前资料", state["report_markdown"])

    def test_old_resident_session_is_normalized_idempotently_on_access(self):
        self._confirm_baseline("resident-old")
        session = intake_sessions.get("resident-old")
        session["context"].pop("baseline_confirmed")
        test_keys = (
            "glucose_tests", "lipid_tests", "uric_acid_test",
            "liver_tests", "kidney_tests", "thyroid_tests",
        )
        for key in test_keys:
            session["field_states"].pop(key)
        session["field_states"]["metabolic_tests"] = {
            "status": "confirmed", "evidence": ["旧版代谢检查已回答"], "confidence": 0.9,
            "attempts": 1, "conflicts": [], "audit": [],
        }
        session.update({
            "phase": "follow_up",
            "current_question": "正在进行的旧版追问",
            "current_field_key": "metabolic_tests",
            "attempt_number": 2,
            "follow_up_answers": [{"question": "旧问题", "answer": "旧回答"}],
            "execution": {"total_score": 99.0},
        })
        active_state = {
            "current_question": session["current_question"],
            "current_field_key": session["current_field_key"],
            "attempt_number": session["attempt_number"],
            "follow_up_answers": deepcopy(session["follow_up_answers"]),
        }

        first = get_intake_state("resident-old")
        second = get_intake_state("resident-old")

        self.assertTrue(first["context"]["baseline_confirmed"])
        self.assertTrue(first["execution"]["baseline_ready"])
        self.assertEqual(first["field_states"]["metabolic_tests"]["evidence"], ["旧版代谢检查已回答"])
        for key in test_keys:
            self.assertEqual(first["field_states"][key]["status"], "not_asked")
            self.assertEqual(first["field_states"][key]["evidence"], [])
            self.assertEqual(first["execution"]["raw_points"][key], 0.0)
        for key, value in active_state.items():
            self.assertEqual(first[key], value)
        self.assertEqual(first["field_states"], second["field_states"])
        self.assertEqual(first["execution"], second["execution"])

    def test_old_resident_incomplete_stop_is_not_left_completed(self):
        self._confirm_baseline("resident-stopped")
        session = intake_sessions.get("resident-stopped")
        session.update({"phase": "completed", "stop_reason": "no_collectable_gap"})

        state = get_intake_state("resident-stopped")

        self.assertEqual(state["phase"], "incomplete")
        self.assertFalse(state["is_complete"])

    def test_old_manual_completion_below_current_gate_is_downgraded(self):
        self._confirm_baseline("resident-manual-low")
        session = intake_sessions.get("resident-manual-low")
        session.update({"phase": "completed", "stop_reason": "manual_completion"})

        state = get_intake_state("resident-manual-low")

        self.assertEqual(state["phase"], "incomplete")
        self.assertFalse(state["is_complete"])
        self.assertEqual(state["stop_reason"], "manual_incomplete")

    def test_old_manual_completion_meeting_current_gate_stays_completed(self):
        self._confirm_baseline("resident-manual-complete")
        session = intake_sessions.get("resident-manual-complete")
        for field in session["field_states"].values():
            if field["status"] != "not_applicable":
                field["status"] = "confirmed"
        session.update({"phase": "completed", "stop_reason": "manual_completion"})

        state = get_intake_state("resident-manual-complete")

        self.assertEqual(state["phase"], "completed")
        self.assertTrue(state["is_complete"])
        self.assertEqual(state["stop_reason"], "manual_completion")

    def test_old_male_session_derives_pregnancy_applicability_and_preserves_history(self):
        set_baseline("resident-male", {
            "age": 42,
            "sex": "male",
            "height_cm": 175,
            "weight_kg": 90,
            "measured_at": "2026-08-18",
        })
        session = intake_sessions.get("resident-male")
        session["context"]["pregnancy_applicable"] = True
        session["field_states"]["pregnancy"].update({
            "status": "partial",
            "evidence": ["旧会话历史信息"],
            "conflicts": [{"turn": 1, "evidence": "待核实"}],
            "audit": [{"turn": 1, "to_status": "partial"}],
        })

        first = get_intake_state("resident-male")
        second = get_intake_state("resident-male")

        self.assertFalse(first["context"]["pregnancy_applicable"])
        self.assertEqual(first["field_states"]["pregnancy"]["status"], "not_applicable")
        self.assertEqual(first["field_states"]["pregnancy"]["evidence"], ["旧会话历史信息"])
        self.assertEqual(first["field_states"]["pregnancy"]["conflicts"], [{"turn": 1, "evidence": "待核实"}])
        self.assertEqual(first["field_states"]["pregnancy"]["audit"], [{"turn": 1, "to_status": "partial"}])
        self.assertEqual(first["execution"]["layer_max"]["safety"], 22.0)
        self.assertEqual(first["field_states"], second["field_states"])
        self.assertEqual(first["execution"], second["execution"])

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
