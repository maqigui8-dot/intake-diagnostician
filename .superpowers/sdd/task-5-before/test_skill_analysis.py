import unittest
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_analysis import (
    analyze_intake_with_agent,
    build_analysis_prompt,
    build_extraction_prompt,
    build_question_prompt,
    extract_local_red_flags,
    process_intake_turn,
    parse_analysis_response,
    parse_extraction_response,
    parse_question_response,
)
from agent import build_llm


SAMPLE_STATE = {
    "summary": {"主要症状": "胃胀、反酸", "持续时间": "几个月以上", "寒热": "比较怕冷"},
    "answers": {},
    "progress": {"answered": 10, "total": 10, "percent": 100},
    "follow_up_answers": [{"question": "反酸什么时候明显？", "answer": "饭后半小时"}],
    "follow_up_count": 1,
}


class FakeAgent:
    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error
        self.last_config = None

    def invoke(self, payload, config):
        self.last_config = config
        if self.error:
            raise self.error
        return {"messages": [type("Message", (), {"type": "ai", "content": self.content})()]}


def confirm_baseline(session_id: str):
    from intake_flow import set_baseline

    set_baseline(session_id, {
        "age": 32,
        "sex": "female",
        "height_cm": 170,
        "weight_kg": 81,
        "measured_at": "2026-08-18",
    })


class SkillAnalysisTests(unittest.TestCase):
    def test_local_red_flag_detection_respects_explicit_negation(self):
        self.assertEqual(extract_local_red_flags("最近有胸痛"), ["胸痛"])
        self.assertEqual(extract_local_red_flags("最近没有胸痛，也没有晕厥"), [])
        self.assertEqual(
            extract_local_red_flags("胸痛偶尔出现，目前没有明显呼吸困难、晕厥或意识异常"),
            ["胸痛"],
        )

    def test_extractor_returns_field_evidence_without_scores(self):
        result = parse_extraction_response(
            '{"field_updates":[{"field_key":"allergies","status":"confirmed",'
            '"evidence":"没有药物过敏","confidence":0.98}],"conflicts":[],"red_flags":[]}'
        )
        self.assertEqual(result["field_updates"][0]["field_key"], "allergies")
        self.assertNotIn("total_score", result)

    def test_extractor_discards_unknown_keys_and_normalizes_values(self):
        result = parse_extraction_response(
            '{"field_updates":['
            '{"field_key":"unknown","status":"confirmed","evidence":"x","confidence":1},'
            '{"field_key":"main_goal","status":"invalid","evidence":"想减重","confidence":9}'
            '],"conflicts":[],"red_flags":[]}'
        )
        self.assertEqual(len(result["field_updates"]), 1)
        self.assertEqual(result["field_updates"][0]["status"], "partial")
        self.assertEqual(result["field_updates"][0]["confidence"], 1.0)

    def test_process_turn_rejects_model_evidence_absent_from_patient_answers(self):
        from intake_flow import intake_sessions, submit_open_answer

        intake_sessions.clear()
        confirm_baseline("unsupported-evidence")
        submit_open_answer("unsupported-evidence", "希望减重，最近体重增加")

        agent = FakeAgent(content=(
            '{"field_updates":[{'
            '"field_key":"allergies","status":"confirmed",'
            '"evidence":"没有药物过敏","confidence":0.98}],'
            '"conflicts":[],"red_flags":[]}'
        ))
        state = process_intake_turn("unsupported-evidence", agent)

        self.assertEqual(state["field_states"]["allergies"]["status"], "not_asked")
        self.assertEqual(state["field_states"]["allergies"]["evidence"], [])

    def test_process_turn_accepts_punctuation_normalized_multi_field_evidence(self):
        from intake_flow import intake_sessions, submit_open_answer

        intake_sessions.clear()
        confirm_baseline("multi-field-evidence")
        submit_open_answer("multi-field-evidence", "三餐不规律；每周，很少运动。")

        agent = FakeAgent(content=(
            '{"field_updates":['
            '{"field_key":"diet_pattern","status":"confirmed",'
            '"evidence":"三餐 不规律","confidence":0.98},'
            '{"field_key":"exercise","status":"confirmed",'
            '"evidence":"每周很少运动","confidence":0.95},'
            '{"field_key":"allergies","status":"confirmed",'
            '"evidence":"没有药物过敏","confidence":0.98}'
            '],"conflicts":[],"red_flags":[]}'
        ))
        state = process_intake_turn("multi-field-evidence", agent)

        self.assertEqual(state["field_states"]["diet_pattern"]["status"], "confirmed")
        self.assertEqual(state["field_states"]["exercise"]["status"], "confirmed")
        self.assertEqual(state["field_states"]["allergies"]["status"], "not_asked")

    def test_extraction_prompt_forbids_ai_scoring_and_diagnosis(self):
        prompt = build_extraction_prompt({"open_answer": "半年胖了十斤", "follow_up_answers": []})
        self.assertIn("成人单纯性肥胖", prompt)
        self.assertIn("不得计算执行度", prompt)
        self.assertIn("不输出证型", prompt)

    def test_question_parser_uses_fallback_for_invalid_output(self):
        self.assertEqual(parse_question_response("不是JSON", "默认安全问题"), "默认安全问题")
        self.assertEqual(parse_question_response('{"question":"请问有药物过敏吗？"}', "默认问题"), "请问有药物过敏吗？")

    def test_question_parser_rejects_instruction_to_pause_intake(self):
        fallback = "请问胸痛现在是否仍在发生，是否伴有呼吸困难或晕厥？"
        generated = '{"question":"建议您先暂停本次线上问诊，尽快线下就医，好吗？"}'
        self.assertEqual(parse_question_response(generated, fallback), fallback)

    def test_question_prompt_contains_one_field_and_retry_number(self):
        prompt = build_question_prompt("allergies", 2, {"open_answer": "想减重", "follow_up_answers": []})
        self.assertIn('"field_key": "allergies"', prompt)
        self.assertIn('"attempt_number": 2', prompt)
        self.assertIn("不得要求患者暂停或结束问诊", prompt)
        self.assertIn("一次只问一个信息点", prompt)

    def test_process_turn_extracts_scores_and_generates_selected_question(self):
        from intake_flow import intake_sessions, submit_open_answer

        class SequenceAgent:
            def __init__(self):
                self.contents = [
                    '{"field_updates":[{"field_key":"main_goal","status":"confirmed","evidence":"想减重","confidence":0.98},{"field_key":"weight_change","status":"confirmed","evidence":"半年胖十斤","confidence":0.95}],"conflicts":[],"red_flags":[]}',
                    '{"question":"为了安全确认一下，最近有没有胸痛、喘不过气或晕倒？"}',
                ]

            def invoke(self, payload, config):
                return {"messages": [type("Message", (), {"type": "ai", "content": self.contents.pop(0)})()]}

        intake_sessions.clear()
        confirm_baseline("turn-a")
        submit_open_answer("turn-a", "想减重，半年胖了十斤")
        state = process_intake_turn("turn-a", SequenceAgent())
        self.assertEqual(state["phase"], "follow_up")
        self.assertEqual(state["current_field_key"], "red_flags")
        self.assertGreater(state["execution"]["total_score"], 0)
        self.assertIn("胸痛", state["current_question"])

    def test_process_turn_marks_detected_red_flag_confirmed_before_selecting_next_field(self):
        from intake_flow import intake_sessions, submit_open_answer

        class RedFlagAgent:
            def __init__(self):
                self.contents = [
                    '{"field_updates":[{"field_key":"main_goal","status":"confirmed","evidence":"想控制体重","confidence":0.98}],"conflicts":[],"red_flags":["胸痛"]}',
                    '{"question":"为了后续用药安全，请问您有明确的药物、食物或其他过敏吗？"}',
                ]

            def invoke(self, payload, config):
                return {"messages": [type("Message", (), {"type": "ai", "content": self.contents.pop(0)})()]}

        intake_sessions.clear()
        confirm_baseline("red-flag-next-field")
        submit_open_answer("red-flag-next-field", "最近半年体重增加二十公斤，而且有胸痛")
        state = process_intake_turn("red-flag-next-field", RedFlagAgent())

        self.assertEqual(state["phase"], "follow_up")
        self.assertEqual(state["field_states"]["red_flags"]["status"], "confirmed")
        self.assertEqual(state["current_field_key"], "allergies")
        self.assertEqual(state["safety_alerts"], ["胸痛"])

    def test_process_turn_locally_detects_red_flag_when_agent_omits_it(self):
        from intake_flow import intake_sessions, submit_open_answer

        class OmissionAgent:
            def __init__(self):
                self.contents = [
                    '{"field_updates":[{"field_key":"main_goal","status":"confirmed","evidence":"想控制体重","confidence":0.98}],"conflicts":[],"red_flags":[]}',
                    '{"question":"为了后续用药安全，请问您有明确的药物、食物或其他过敏吗？"}',
                ]

            def invoke(self, payload, config):
                return {"messages": [type("Message", (), {"type": "ai", "content": self.contents.pop(0)})()]}

        intake_sessions.clear()
        confirm_baseline("local-red-flag")
        submit_open_answer("local-red-flag", "最近半年体重增加二十公斤，而且有胸痛")
        state = process_intake_turn("local-red-flag", OmissionAgent())

        self.assertEqual(state["field_states"]["red_flags"]["status"], "confirmed")
        self.assertEqual(state["current_field_key"], "allergies")
        self.assertEqual(state["safety_alerts"], ["胸痛"])

    def test_process_turn_uses_fixed_safety_question_when_ai_is_unavailable(self):
        from intake_flow import intake_sessions, submit_open_answer

        intake_sessions.clear()
        confirm_baseline("turn-b")
        submit_open_answer("turn-b", "想控制体重，身高165厘米，体重85公斤，半年增加十斤")
        state = process_intake_turn("turn-b", FakeAgent(error=RuntimeError("offline")))
        self.assertEqual(state["phase"], "follow_up")
        self.assertEqual(state["current_field_key"], "red_flags")
        self.assertIn("胸痛", state["current_question"])
        self.assertEqual(state["field_states"]["main_goal"]["status"], "confirmed")
        self.assertEqual(state["field_states"]["height_weight"]["status"], "confirmed")
        self.assertGreater(state["execution"]["total_score"], 0)

    def test_offline_irrelevant_answer_does_not_confirm_current_safety_field(self):
        from intake_flow import intake_sessions, submit_follow_up_answer

        intake_sessions.clear()
        confirm_baseline("offline-irrelevant-answer")
        session = intake_sessions.get("offline-irrelevant-answer")
        session["field_states"]["red_flags"]["status"] = "confirmed"
        session.update({
            "phase": "follow_up",
            "current_question": "您有明确的药物或食物过敏吗？",
            "current_field_key": "allergies",
            "attempt_number": 1,
        })
        submit_follow_up_answer("offline-irrelevant-answer", "今天天气不错")

        state = process_intake_turn("offline-irrelevant-answer", FakeAgent(error=RuntimeError("offline")))

        self.assertEqual(state["field_states"]["allergies"]["status"], "partial")
        self.assertEqual(state["field_states"]["allergies"]["attempts"], 1)
        self.assertEqual(state["current_field_key"], "allergies")
        self.assertEqual(state["attempt_number"], 2)

    def test_offline_second_irrelevant_answer_advances_without_confirming_field(self):
        from intake_flow import intake_sessions, submit_follow_up_answer

        intake_sessions.clear()
        confirm_baseline("offline-second-irrelevant-answer")
        session = intake_sessions.get("offline-second-irrelevant-answer")
        session["field_states"]["red_flags"]["status"] = "confirmed"
        session.update({
            "phase": "follow_up",
            "current_question": "您有明确的药物或食物过敏吗？",
            "current_field_key": "allergies",
            "attempt_number": 1,
        })
        submit_follow_up_answer("offline-second-irrelevant-answer", "今天天气不错")
        process_intake_turn("offline-second-irrelevant-answer", FakeAgent(error=RuntimeError("offline")))
        submit_follow_up_answer("offline-second-irrelevant-answer", "还是今天天气不错")

        state = process_intake_turn("offline-second-irrelevant-answer", FakeAgent(error=RuntimeError("offline")))

        self.assertEqual(state["field_states"]["allergies"]["status"], "partial")
        self.assertEqual(state["field_states"]["allergies"]["attempts"], 2)
        self.assertEqual(state["current_field_key"], "medications")

    def test_offline_unrelated_mention_of_medicine_does_not_confirm_medications(self):
        from intake_flow import intake_sessions, submit_follow_up_answer

        intake_sessions.clear()
        confirm_baseline("offline-unrelated-medicine")
        session = intake_sessions.get("offline-unrelated-medicine")
        session["field_states"]["red_flags"]["status"] = "confirmed"
        session["field_states"]["allergies"]["status"] = "confirmed"
        session.update({
            "phase": "follow_up",
            "current_question": "您目前正在使用哪些药物？",
            "current_field_key": "medications",
            "attempt_number": 1,
        })
        submit_follow_up_answer("offline-unrelated-medicine", "我喜欢中药诗")

        state = process_intake_turn("offline-unrelated-medicine", FakeAgent(error=RuntimeError("offline")))

        self.assertEqual(state["field_states"]["medications"]["status"], "partial")
        self.assertEqual(state["current_field_key"], "medications")

    def test_offline_direct_negative_confirms_each_current_safety_field(self):
        from intake_flow import intake_sessions, submit_follow_up_answer

        safety_keys = ("red_flags", "allergies", "medications", "important_history")
        for key in safety_keys:
            with self.subTest(field_key=key):
                intake_sessions.clear()
                confirm_baseline(f"offline-direct-negative-{key}")
                session = intake_sessions.get(f"offline-direct-negative-{key}")
                for other_key in safety_keys:
                    if other_key != key:
                        session["field_states"][other_key]["status"] = "confirmed"
                session["field_states"]["pregnancy"]["status"] = "confirmed"
                session.update({
                    "phase": "follow_up",
                    "current_question": "请确认是否有相关情况。",
                    "current_field_key": key,
                    "attempt_number": 1,
                })
                submit_follow_up_answer(f"offline-direct-negative-{key}", "没有")

                state = process_intake_turn(
                    f"offline-direct-negative-{key}", FakeAgent(error=RuntimeError("offline"))
                )

                self.assertEqual(state["field_states"][key]["status"], "confirmed")
                self.assertEqual(state["field_states"][key]["evidence"], ["没有"])

    def test_offline_open_clarification_skips_local_basic_extraction(self):
        from intake_flow import intake_sessions, submit_open_answer

        intake_sessions.clear()
        confirm_baseline("offline-open-clarification")
        submit_open_answer("offline-open-clarification", "想减重是什么意思？")

        state = process_intake_turn("offline-open-clarification", FakeAgent(error=RuntimeError("offline")))

        self.assertEqual(state["field_states"]["main_goal"]["status"], "not_asked")
        self.assertEqual(state["field_states"]["main_goal"]["evidence"], [])

    def test_open_clarification_is_not_model_evidence(self):
        from intake_flow import intake_sessions, submit_open_answer

        intake_sessions.clear()
        confirm_baseline("open-clarification-evidence")
        submit_open_answer("open-clarification-evidence", "这是什么意思？")

        agent = FakeAgent(content=(
            '{"field_updates":[{'
            '"field_key":"main_goal","status":"confirmed",'
            '"evidence":"这是什么意思","confidence":0.99}],'
            '"conflicts":[],"red_flags":[]}'
        ))
        state = process_intake_turn("open-clarification-evidence", agent)

        self.assertEqual(state["field_states"]["main_goal"]["status"], "not_asked")
        self.assertEqual(state["field_states"]["main_goal"]["evidence"], [])

    def test_process_turn_discards_model_updates_for_clarification_request(self):
        from intake_flow import intake_sessions, submit_follow_up_answer

        class ClarificationAgent:
            def invoke(self, payload, config):
                return {"messages": [type("Message", (), {"type": "ai", "content": (
                    '{"field_updates":['
                    '{"field_key":"allergies","status":"confirmed","evidence":"这是什么","confidence":0.99},'
                    '{"field_key":"main_goal","status":"confirmed","evidence":"这是什么","confidence":0.99}'
                    '],"conflicts":[],"red_flags":[]}'
                )})()]}

        intake_sessions.clear()
        confirm_baseline("clarification-model-output")
        session = intake_sessions.get("clarification-model-output")
        session["field_states"]["red_flags"]["status"] = "confirmed"
        session.update({
            "phase": "follow_up",
            "current_question": "您有明确的药物或食物过敏吗？",
            "current_field_key": "allergies",
            "attempt_number": 1,
        })
        submit_follow_up_answer("clarification-model-output", "这是什么意思？")

        state = process_intake_turn("clarification-model-output", ClarificationAgent())

        self.assertEqual(state["field_states"]["allergies"]["status"], "not_asked")
        self.assertEqual(state["field_states"]["main_goal"]["status"], "not_asked")
        self.assertEqual(state["current_field_key"], "allergies")
        self.assertIn("解释", state["current_question"])

    def test_clarification_with_red_flag_word_creates_no_safety_evidence(self):
        from intake_flow import intake_sessions, submit_follow_up_answer

        agent = FakeAgent(content='{"field_updates":[],"conflicts":[],"red_flags":[]}')
        intake_sessions.clear()
        confirm_baseline("clarification-red-flag-word")
        session = intake_sessions.get("clarification-red-flag-word")
        session.update({
            "phase": "follow_up",
            "current_question": "最近有没有胸痛、明显呼吸困难或晕厥？",
            "current_field_key": "red_flags",
            "attempt_number": 1,
        })
        submit_follow_up_answer("clarification-red-flag-word", "胸痛是什么意思？")

        state = process_intake_turn("clarification-red-flag-word", agent)

        self.assertEqual(state["field_states"]["red_flags"]["status"], "not_asked")
        self.assertEqual(state["field_states"]["red_flags"]["evidence"], [])
        self.assertEqual(state["safety_alerts"], [])
        self.assertEqual(state["current_field_key"], "red_flags")
        self.assertIn("解释", state["current_question"])

    def test_process_turn_keeps_persisted_red_flags_when_building_final_exams(self):
        from intake_flow import intake_sessions

        intake_sessions.clear()
        confirm_baseline("persisted-alert")
        session = intake_sessions.get("persisted-alert")
        session.update({
            "phase": "processing",
            "open_answer": "最近半年体重增加二十公斤",
            "safety_alerts": ["胸痛"],
        })
        for field in session["field_states"].values():
            if field["status"] != "not_applicable":
                field.update({"status": "confirmed", "evidence": ["已确认"], "confidence": 0.95})

        agent = FakeAgent(content='{"field_updates":[],"conflicts":[],"red_flags":[]}')
        state = process_intake_turn("persisted-alert", agent)

        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["safety_alerts"], ["胸痛"])
        self.assertEqual(state["recommended_exams"], [])

    def test_online_extractor_cannot_skip_the_single_polite_retry(self):
        from intake_flow import intake_sessions, submit_follow_up_answer

        class RetryAgent:
            def __init__(self):
                self.contents = [
                    '{"field_updates":[{"field_key":"red_flags","status":"unavailable","evidence":"不知道","confidence":0.99}],"conflicts":[],"red_flags":[]}',
                    '{"question":"为了安全再确认一次：近期是否出现胸痛、喘不过气、晕倒或意识不清？"}',
                ]

            def invoke(self, payload, config):
                return {"messages": [type("Message", (), {"type": "ai", "content": self.contents.pop(0)})()]}

        intake_sessions.clear()
        confirm_baseline("retry-online")
        session = intake_sessions.get("retry-online")
        session.update({
            "phase": "follow_up", "current_question": "最近有胸痛吗？",
            "current_field_key": "red_flags", "attempt_number": 1,
        })
        submit_follow_up_answer("retry-online", "不知道")
        state = process_intake_turn("retry-online", RetryAgent())
        self.assertEqual(state["current_field_key"], "red_flags")
        self.assertEqual(state["attempt_number"], 2)
        self.assertEqual(state["field_states"]["red_flags"]["status"], "partial")

    def test_prompt_uses_question_selection_and_questioning_skills(self):
        prompt = build_analysis_prompt(SAMPLE_STATE)
        self.assertIn("tcm-intake-checklist", prompt)
        self.assertIn("tcm-questioning-guide", prompt)
        self.assertIn("后续诊中", prompt)
        self.assertNotIn("tcm-zhengxing", prompt)
        self.assertIn("只输出 JSON", prompt)
        self.assertIn("饭后半小时", prompt)
        self.assertIn("最多输出一个补问问题", prompt)

    def test_parse_new_analysis_schema(self):
        text = '''```json
        {
          "completeness_status":"needs_follow_up",
          "completeness_summary":"基础信息已采集，但症状特征不足",
          "missing_required_items":["反酸发生时间"],
          "optional_items":["既往胃镜结果"],
          "follow_up_key":"reflux_timing",
          "follow_up_kind":"required",
          "follow_up_questions":["您的反酸通常在饭前还是饭后更明显？"],
          "safety_alerts":[],
          "recommended_exams":[{"name":"胃镜检查","type":"仪器","department":"消化内科","reason":"症状持续数月，用于观察上消化道情况","priority":"routine","precautions":"按医院要求空腹"}]
        }
        ```'''
        result = parse_analysis_response(text)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["completeness_status"], "needs_follow_up")
        self.assertEqual(result["missing_required_items"], ["反酸发生时间"])
        self.assertEqual(result["follow_up_key"], "reflux_timing")
        self.assertEqual(result["follow_up_kind"], "required")
        self.assertEqual(result["recommended_exams"][0]["name"], "胃镜检查")
        self.assertEqual(result["recommended_exams"][0]["type"], "仪器")
        self.assertEqual(result["recommended_exams"][0]["department"], "消化内科")
        self.assertEqual(result["recommended_exams"][0]["precautions"], "按医院要求空腹")
        self.assertNotIn("syndrome_reference", result)
        self.assertIn("不能替代", result["disclaimer"])

    def test_invalid_response_returns_unavailable_result(self):
        result = parse_analysis_response("这不是 JSON")
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["missing_required_items"], [])
        self.assertEqual(result["recommended_exams"], [])
        self.assertNotIn("syndrome_reference", result)

    def test_agent_failure_does_not_raise(self):
        result = analyze_intake_with_agent("session-a", SAMPLE_STATE, FakeAgent(error=RuntimeError("offline")))
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("基础档案已正常生成", result["message"])

    def test_analysis_uses_isolated_thread(self):
        agent = FakeAgent(content='{"completeness_status":"complete","completeness_summary":"信息充分","missing_required_items":[],"optional_items":[],"follow_up_questions":[],"safety_alerts":[],"recommended_exams":[]}')
        result = analyze_intake_with_agent("session-a", SAMPLE_STATE, agent)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(agent.last_config["configurable"]["thread_id"], "structured-analysis-session-a")

    def test_agent_result_is_stopped_when_gap_was_already_attempted(self):
        content = '{"completeness_status":"needs_follow_up","completeness_summary":"仍缺信息","missing_required_items":["反酸时间"],"optional_items":[],"follow_up_key":"reflux_timing","follow_up_kind":"required","follow_up_questions":["反酸通常什么时候明显？"],"safety_alerts":[],"recommended_exams":[]}'
        state = {
            **SAMPLE_STATE,
            "follow_up_answers": [
                {"question_key": "reflux_timing", "question": "反酸何时明显？", "answer": "不知道"}
            ],
            "follow_up_count": 1,
        }
        result = analyze_intake_with_agent("session-a", state, FakeAgent(content=content))
        self.assertEqual(result["follow_up_questions"], [])
        self.assertEqual(result["completion_reason"], "duplicate_gap")


class ApiIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_patient_session_endpoint_does_not_return_internal_scores(self):
        import main
        from intake_flow import intake_sessions

        intake_sessions.clear()
        result = await main.get_structured_intake("public-a")
        self.assertEqual(result["phase"], "baseline_collection")
        self.assertNotIn("execution", result)
        self.assertNotIn("field_states", result)

    async def test_open_answer_endpoint_returns_processing_state(self):
        import main
        from intake_flow import intake_sessions

        intake_sessions.clear()
        confirm_baseline("public-b")
        result = await main.answer_open_intake("public-b", main.IntakeOpenAnswerRequest(answer="半年胖了十斤"))
        self.assertEqual(result["phase"], "processing")
        self.assertEqual(result["open_answer"], "半年胖了十斤")

    async def test_doctor_endpoint_contains_execution_summary(self):
        import main
        from intake_flow import intake_sessions

        intake_sessions.clear()
        result = await main.get_doctor_intake_summary("doctor-a")
        self.assertEqual(result["access_scope"], "prototype_doctor_view")
        self.assertIn("execution", result)

    async def test_analysis_endpoint_processes_turn_and_returns_patient_safe_state(self):
        import main
        from intake_flow import get_intake_state, intake_sessions

        intake_sessions.clear()
        confirm_baseline("session-a")
        internal = get_intake_state("session-a")
        internal.update({"phase": "follow_up", "current_question": "最近有胸痛吗？", "current_field_key": "red_flags", "attempt_number": 1})
        with patch.object(main, "get_analysis_agent", return_value=object()), patch.object(main, "process_intake_turn", return_value=internal) as process:
            result = await main.analyze_structured_intake("session-a")
        self.assertEqual(result["phase"], "follow_up")
        self.assertNotIn("execution", result)
        process.assert_called_once_with("session-a", unittest.mock.ANY)

    async def test_analysis_timeout_returns_retryable_unavailable_result(self):
        import main
        from intake_flow import intake_sessions

        def slow_analysis(*args):
            time.sleep(0.05)
            return {"status": "completed"}

        intake_sessions.clear()
        confirm_baseline("session-a")
        with patch.object(main, "ANALYSIS_TIMEOUT_SECONDS", 0.001), patch.object(main, "get_analysis_agent", return_value=object()), patch.object(main, "process_intake_turn", side_effect=slow_analysis):
            result = await main.analyze_structured_intake("session-a")

        self.assertEqual(result["phase"], "follow_up")
        self.assertIn("胸痛", result["next_question"])

    async def test_save_request_keeps_skill_analysis(self):
        import main
        req = main.SaveRecordRequest(session_id="session-a", structured_answers={"chief_complaint": {"option_label": "胃胀"}}, follow_up_answers=[{"question": "何时明显？", "answer": "饭后"}], skill_analysis={"status": "completed", "completeness_status": "complete"})
        self.assertEqual(req.skill_analysis["completeness_status"], "complete")
        self.assertEqual(req.follow_up_answers[0]["answer"], "饭后")

    async def test_save_endpoint_rejects_incomplete_session_despite_client_payload(self):
        import main
        from intake_flow import intake_sessions

        intake_sessions.clear()
        confirm_baseline("save-incomplete")
        session = intake_sessions.get("save-incomplete")
        session.update({"phase": "incomplete", "stop_reason": "manual_incomplete"})
        req = main.SaveRecordRequest(
            session_id="save-incomplete",
            collected_info={"client_claim": "complete"},
            skill_analysis={"completeness_status": "complete"},
        )

        with patch.object(main, "save_record_to_file") as save_file:
            with self.assertRaises(main.HTTPException) as error:
                await main.save_record(req)

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("资料尚未达到完整条件", error.exception.detail)
        save_file.assert_not_called()

    async def test_save_endpoint_rejects_completed_phase_below_current_threshold(self):
        import main
        from intake_flow import intake_sessions

        intake_sessions.clear()
        confirm_baseline("save-stale-completed")
        session = intake_sessions.get("save-stale-completed")
        session.update({"phase": "completed", "stop_reason": "threshold_reached"})

        with patch.object(main, "save_record_to_file") as save_file:
            with self.assertRaises(main.HTTPException) as error:
                await main.save_record(main.SaveRecordRequest(session_id="save-stale-completed"))

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("资料尚未达到完整条件", error.exception.detail)
        save_file.assert_not_called()

    async def test_save_endpoint_accepts_completed_session_meeting_current_threshold(self):
        import main
        from intake_flow import intake_sessions

        intake_sessions.clear()
        confirm_baseline("save-complete")
        session = intake_sessions.get("save-complete")
        for field in session["field_states"].values():
            if field["status"] != "not_applicable":
                field["status"] = "confirmed"
        session.update({"phase": "completed", "stop_reason": "threshold_reached"})

        with patch.object(main, "save_record_to_file") as save_file:
            result = await main.save_record(main.SaveRecordRequest(session_id="save-complete"))

        self.assertTrue(result["record_id"])
        save_file.assert_called_once()

    async def test_follow_up_endpoint_updates_current_session(self):
        import main
        from intake_flow import intake_sessions

        intake_sessions.clear()
        confirm_baseline("session-a")
        session = intake_sessions.get("session-a")
        session.update({"phase": "follow_up", "current_question": "有药物过敏吗？", "current_field_key": "allergies", "attempt_number": 1})
        result = await main.answer_structured_follow_up("session-a", main.IntakeFollowUpRequest(answer="没有"))
        self.assertEqual(result["phase"], "processing")
        self.assertEqual(result["follow_up_count"], 1)


class AnalysisAgentTests(unittest.TestCase):
    def test_analysis_agent_injects_both_skill_contents_in_one_model_call(self):
        from agent import IntakeAnalysisAgent

        class FakeLlm:
            def __init__(self):
                self.messages = None

            def invoke(self, messages, config=None):
                self.messages = messages
                return type("Message", (), {"type": "ai", "content": "{}"})()

        llm = FakeLlm()
        agent = IntakeAnalysisAgent(llm=llm)
        result = agent.invoke({"messages": [type("Message", (), {"content": "检查资料"})()]}, {})

        system_content = llm.messages[0].content
        self.assertIn("成人单纯性肥胖诊前资料检查", system_content)
        self.assertIn("成人肥胖诊前追问表达指南", system_content)
        self.assertEqual(result["messages"][0].content, "{}")


class SkillConfigurationTests(unittest.TestCase):
    def test_skills_are_scoped_to_obesity_execution_and_patient_safe_language(self):
        backend_dir = Path(__file__).resolve().parents[1]
        checklist = (backend_dir / "skills" / "tcm-intake-checklist" / "SKILL.md").read_text(encoding="utf-8")
        questioning = (backend_dir / "skills" / "tcm-questioning-guide" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("成人单纯性肥胖", "辨证资料执行度", "开方安全执行度", "AI 不直接计分"):
            self.assertIn(phrase, checklist)
        for phrase in ("开放式首问", "每轮一个信息点", "只允许委婉重问一次", "不得向患者展示"):
            self.assertIn(phrase, questioning)

    def test_analysis_and_questioning_skill_do_not_use_a_fixed_round_limit(self):
        backend_dir = Path(__file__).resolve().parents[1]
        prompt_source = (backend_dir / "skill_analysis.py").read_text(encoding="utf-8")
        skill_source = (backend_dir / "skills" / "tcm-questioning-guide" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("max_follow_up_answers", prompt_source)
        self.assertNotIn("最多进行 5 轮", skill_source)

    def test_questioning_skill_keeps_collecting_after_a_red_flag(self):
        backend_dir = Path(__file__).resolve().parents[1]
        skill_source = (backend_dir / "skills" / "tcm-questioning-guide" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("停止普通追问", skill_source)
        self.assertIn("继续采集诊前资料", skill_source)

    def test_skills_distinguish_rule_scoring_from_patient_questioning(self):
        backend_dir = Path(__file__).resolve().parents[1]
        checklist = (backend_dir / "skills" / "tcm-intake-checklist" / "SKILL.md").read_text(encoding="utf-8")
        questioning = (backend_dir / "skills" / "tcm-questioning-guide" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("最终分数与停止规则由程序", checklist)
        self.assertIn("第二次仍无法回答时停止询问该字段", questioning)

    def test_analysis_uses_a_separate_non_conversational_agent(self):
        backend_dir = Path(__file__).resolve().parents[1]
        agent_source = (backend_dir / "agent.py").read_text(encoding="utf-8")
        main_source = (backend_dir / "main.py").read_text(encoding="utf-8")
        self.assertIn("def create_intake_analysis_agent", agent_source)
        self.assertIn("ANALYSIS_SYSTEM_PROMPT", agent_source)
        self.assertIn("get_analysis_agent()", main_source)

    def test_frontend_has_no_right_side_basic_question_list(self):
        project_dir = Path(__file__).resolve().parents[2]
        app_source = (project_dir / "frontend" / "src" / "App.vue").read_text(encoding="utf-8")
        self.assertNotIn('<section class="panel required-card">', app_source)

    def test_frontend_continues_through_server_side_fallback_without_manual_retry(self):
        project_dir = Path(__file__).resolve().parents[2]
        app_source = (project_dir / "frontend" / "src" / "App.vue").read_text(encoding="utf-8")
        self.assertNotIn("重新分析", app_source)
        self.assertIn("analyzeTurn", app_source)

    def test_new_question_skills_exist_and_agent_loads_them(self):
        backend_dir = Path(__file__).resolve().parents[1]
        checklist = backend_dir / "skills" / "tcm-intake-checklist" / "SKILL.md"
        questioning = backend_dir / "skills" / "tcm-questioning-guide" / "SKILL.md"
        self.assertTrue(checklist.exists())
        self.assertTrue(questioning.exists())
        agent_source = (backend_dir / "agent.py").read_text(encoding="utf-8")
        self.assertIn('str(_skills_dir / "tcm-intake-checklist")', agent_source)
        self.assertIn('str(_skills_dir / "tcm-questioning-guide")', agent_source)
        self.assertNotIn('str(_skills_dir / "tcm-zhengxing")', agent_source)


class ModelConfigurationTests(unittest.TestCase):
    def test_deepseek_key_selects_v4_flash(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-deepseek-key"}, clear=True):
            llm = build_llm()

        self.assertEqual(llm.model_name, "deepseek-v4-flash")
        self.assertEqual(llm.openai_api_base, "https://api.deepseek.com")

    def test_missing_deepseek_key_falls_back_to_ollama(self):
        with patch.dict(os.environ, {}, clear=True):
            llm = build_llm()

        self.assertEqual(llm.model_name, "qwen3:8b")
        self.assertEqual(llm.openai_api_base, "http://localhost:11434/v1")


if __name__ == "__main__":
    unittest.main()
