"""Run a fixed synthetic regression set against local intake rules only."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from intake_execution import PATIENT_CORE_FIELD_KEYS, blank_field_states, calculate_execution
from intake_question_policy import decide_stop
from skill_analysis import extract_local_follow_up_field, extract_local_red_flags


CASE_FILE = Path(__file__).with_name("cases.json")


def load_cases() -> list[dict[str, Any]]:
    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("评测集必须是病例列表")
    return cases


def _run_case(case: dict[str, Any]) -> Any:
    kind = case["kind"]
    if kind == "field":
        update = extract_local_follow_up_field(case["field_key"], case["text"])
        return bool(update and update.get("status") == "confirmed")
    if kind == "red_flag":
        return extract_local_red_flags(case["text"])
    if kind == "stop":
        context = {"baseline_confirmed": True, "pregnancy_applicable": False}
        states = blank_field_states(context)
        for key in PATIENT_CORE_FIELD_KEYS:
            if states[key]["status"] != "not_applicable":
                states[key]["status"] = "confirmed"
        for key, overrides in case.get("field_overrides", {}).items():
            states[key].update(overrides)
        decision = decide_stop(states, calculate_execution(states, context), [], context, ai_available=False)
        return {key: decision.get(key) for key in case["expected"]}
    raise ValueError(f"未知评测类型: {kind}")


def evaluate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    seen = set()
    categories: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0})
    failures = []
    for case in cases:
        case_id = str(case["id"])
        if case_id in seen:
            raise ValueError(f"重复病例 ID: {case_id}")
        seen.add(case_id)
        if case.get("synthetic") is not True:
            raise ValueError(f"病例未标记为合成数据: {case_id}")
        category = str(case["category"])
        categories[category]["total"] += 1
        actual = _run_case(case)
        if actual == case["expected"]:
            categories[category]["passed"] += 1
        else:
            failures.append({"id": case_id, "expected": case["expected"], "actual": actual})
    return {
        "mode": "offline_deterministic_rules_only",
        "total": len(cases),
        "passed": len(cases) - len(failures),
        "failed_ids": [item["id"] for item in failures],
        "failures": failures,
        "by_category": dict(sorted(categories.items())),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_cases(load_cases()), ensure_ascii=False, indent=2))
