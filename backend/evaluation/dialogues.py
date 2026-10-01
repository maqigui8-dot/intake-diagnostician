"""Fixed synthetic multi-turn conversations using the offline rule fallback.

These runs do not invoke a remote model and are not a clinical validation set.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from intake_flow import (
    configure_intake_repository,
    get_internal_intake_state,
    intake_sessions,
    set_baseline,
    submit_follow_up_answer,
    submit_open_answer,
)
from skill_analysis import process_intake_turn


DEFAULT_ANSWERS = {
    "weight_change": "最近半年体重增加了10斤",
    "onset_course": "大约半年",
    "related_factors": "饮食变多，运动变少",
    "previous_weight_management": "没有尝试过减重",
    "appetite_thirst": "食欲变大",
    "stool_urine": "大便和小便没有明显变化",
    "sleep_emotion": "睡眠正常",
    "fatigue_activity": "容易疲乏",
    "diet_pattern": "三餐规律",
    "exercise": "每周运动两次",
    "sleep_schedule": "作息规律，晚上十一点睡",
    "glucose_tests": "最近没有做过血糖血脂等检查",
    "allergies": "没有",
    "medications": "没有",
    "important_history": "没有",
    "red_flags": "没有",
    "pregnancy": "没有怀孕",
}

BASE_DESCRIPTIONS = (
    "最近半年体重增加了10斤，想改善体重。",
    "这一年体重上涨，平时活动较少，想改善体重。",
    "近三个月体重增加，食欲比以前大，想减重。",
    "半年以来体重上升，晚上常吃夜宵，想控制体重。",
    "最近体重增加，工作久坐，想改善体重。",
    "过去一年逐渐胖了，睡眠不规律，想减重。",
)

VARIANTS = (
    ("routine", {}, "completed", []),
    ("medication", {"medications": "每天服用降压药"}, "completed", []),
    ("allergy", {"allergies": "青霉素过敏"}, "completed", []),
    ("unknown-medication", {"medications": "不清楚"}, "incomplete", []),
    ("chest-pain", {"red_flags": "最近有胸痛"}, "completed", ["胸痛"]),
)


class _OfflineAgent:
    def invoke(self, payload, config=None):
        raise RuntimeError("offline evaluation: LLM intentionally unavailable")


def build_dialogue_cases() -> list[dict[str, Any]]:
    return [
        {
            "id": f"dialogue-{base_index + 1:02d}-{variant_name}",
            "synthetic": True,
            "sex": "female" if base_index % 2 else "male",
            "open_answer": description,
            "answer_overrides": dict(overrides),
            "expected_phase": phase,
            "expected_red_flags": list(red_flags),
        }
        for base_index, description in enumerate(BASE_DESCRIPTIONS)
        for variant_name, overrides, phase, red_flags in VARIANTS
    ]


def _run_dialogue(case: dict[str, Any]) -> dict[str, Any]:
    session_id = f"evaluation-{case['id']}"
    set_baseline(session_id, {
        "age": 35,
        "sex": case["sex"],
        "height_cm": 170,
        "weight_kg": 84,
        "measured_at": "2026-10-01",
    })
    submit_open_answer(session_id, case["open_answer"])
    agent = _OfflineAgent()
    questions: list[str] = []
    for _ in range(40):
        state = process_intake_turn(session_id, agent)
        if state["phase"] != "follow_up":
            break
        key = get_internal_intake_state(session_id)["current_field_key"]
        questions.append(key)
        answer = case["answer_overrides"].get(key, DEFAULT_ANSWERS.get(key))
        if answer is None:
            raise ValueError(f"缺少字段 {key} 的合成回答")
        submit_follow_up_answer(session_id, answer)
    else:
        raise RuntimeError("超过 40 轮，未能停止问诊")

    observed_red_flags = list(state.get("safety_alerts") or [])
    count = Counter(questions)
    no_overquestioning = all(amount <= 2 for amount in count.values())
    red_flags_found = all(flag in observed_red_flags for flag in case["expected_red_flags"])
    return {
        "id": case["id"],
        "phase": state["phase"],
        "stop_reason": state.get("stop_reason"),
        "rounds": len(questions),
        "duplicate_over_limit": not no_overquestioning,
        "red_flags_found": red_flags_found,
        "passed": (
            state["phase"] == case["expected_phase"]
            and no_overquestioning
            and red_flags_found
        ),
    }


def evaluate_dialogues(cases: list[dict[str, Any]]) -> dict[str, Any]:
    configure_intake_repository(None)
    intake_sessions.clear()
    results = []
    for case in cases:
        if case.get("synthetic") is not True:
            raise ValueError(f"非合成病例: {case.get('id')}")
        try:
            results.append(_run_dialogue(case))
        except Exception as error:
            results.append({
                "id": case["id"], "phase": "error", "rounds": 0,
                "red_flags_found": False, "passed": False, "error": str(error),
            })
    positives = [case["id"] for case in cases if case["expected_red_flags"]]
    matched = sum(
        result["red_flags_found"] for result in results if result["id"] in positives
    )
    return {
        "mode": "offline_multi_turn_without_llm",
        "total": len(cases),
        "passed": sum(result["passed"] for result in results),
        "failed_ids": [result["id"] for result in results if not result["passed"]],
        "red_flag_recall": matched / len(positives) if positives else None,
        "mean_rounds": round(sum(result["rounds"] for result in results) / len(results), 2) if results else 0,
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_dialogues(build_dialogue_cases()), ensure_ascii=False, indent=2))
