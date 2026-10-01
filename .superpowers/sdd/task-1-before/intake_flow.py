from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from intake_execution import blank_field_states, calculate_execution, merge_field_updates
from intake_question_policy import question_for_field
from obesity_intake_schema import FIELD_DEFINITIONS, RULE_VERSION


OPEN_QUESTION = "这次您最想改善的体重或身体方面的困扰是什么？可以说说什么时候开始，以及最近有什么变化。"
UNAVAILABLE_MARKERS = ("不知道", "不清楚", "不记得", "说不清", "不方便", "不想说", "拒绝")


class IntakeSessionStore:
    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}

    def clear(self):
        self._sessions.clear()

    def get(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._sessions:
            context: dict[str, object] = {"pregnancy_applicable": True}
            field_states = blank_field_states(context)
            self._sessions[session_id] = {
                "session_id": session_id,
                "phase": "open_intake",
                "context": context,
                "open_question": OPEN_QUESTION,
                "open_answer": "",
                "latest_answer": "",
                "current_question": "",
                "current_field_key": "",
                "attempt_number": 0,
                "turn": 0,
                "follow_up_answers": [],
                "field_states": field_states,
                "execution": calculate_execution(field_states, context),
                "blocking_keys": [],
                "conflicts": [],
                "safety_alerts": [],
                "recommended_exams": [],
                "stop_reason": None,
                "report_markdown": None,
                "audit": [{"event": "session_created", "turn": 0, "rule_version": RULE_VERSION}],
            }
        return self._sessions[session_id]


intake_sessions = IntakeSessionStore()


def get_intake_state(session_id: str) -> dict[str, Any]:
    session = intake_sessions.get(session_id)
    state = deepcopy(session)
    state.update({
        "follow_up_count": len(session["follow_up_answers"]),
        "is_complete": session["phase"] in {"completed", "escalated"},
        "summary": _build_summary(session),
        "answers": {},
        "progress": _build_progress(session),
        "stages": _build_stages(session),
        "assistant_note": _assistant_note(session),
    })
    return state


def get_internal_intake_state(session_id: str) -> dict[str, Any]:
    return intake_sessions.get(session_id)


def submit_open_answer(session_id: str, answer: str) -> dict[str, Any]:
    clean_answer = answer.strip()
    if not clean_answer:
        raise ValueError("开放回答不能为空")
    session = intake_sessions.get(session_id)
    session.update({
        "phase": "processing",
        "open_answer": clean_answer,
        "latest_answer": clean_answer,
        "current_question": "",
        "current_field_key": "",
        "attempt_number": 0,
        "turn": session["turn"] + 1,
        "stop_reason": None,
        "report_markdown": None,
        "recommended_exams": [],
    })
    session["audit"].append({"event": "open_answer_submitted", "turn": session["turn"]})
    return get_intake_state(session_id)


def submit_follow_up_answer(
    session_id: str,
    answer: str,
    legacy_answer: str | None = None,
    *,
    question_key: str = "",
    question_kind: str = "required",
    attempt_number: int | None = None,
) -> dict[str, Any]:
    session = intake_sessions.get(session_id)
    if legacy_answer is None:
        question = session.get("current_question", "")
        clean_answer = answer.strip()
        key = session.get("current_field_key", "")
    else:
        question = answer.strip()
        clean_answer = legacy_answer.strip()
        key = question_key.strip() or session.get("current_field_key", "")

    if not question:
        raise ValueError("当前没有可回答的追问")
    if not clean_answer:
        raise ValueError("补充回答不能为空")
    if not key:
        raise ValueError("当前追问缺少服务端字段标识")

    previous_attempts = sum(1 for item in session["follow_up_answers"] if item.get("question_key") == key)
    current_attempt = attempt_number or session.get("attempt_number") or (previous_attempts + 1)
    current_attempt = max(previous_attempts + 1, int(current_attempt))
    if current_attempt > 2:
        raise ValueError("该项信息已经确认两次，将留给医生诊中核实")

    quality = "unavailable" if _answer_is_unavailable(clean_answer) else "provided"
    session["follow_up_answers"].append({
        "question": question,
        "answer": clean_answer,
        "question_key": key,
        "question_kind": question_kind,
        "attempt_number": current_attempt,
        "answer_quality": quality,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    field = session["field_states"].get(key)
    if field is not None:
        field["attempts"] = current_attempt
        if quality == "unavailable":
            field["status"] = "unavailable" if current_attempt >= 2 else "partial"

    session.update({
        "phase": "processing",
        "latest_answer": clean_answer,
        "current_question": "",
        "current_field_key": "",
        "attempt_number": 0,
        "turn": session["turn"] + 1,
        "stop_reason": None,
        "report_markdown": None,
    })
    session["audit"].append({
        "event": "follow_up_answer_submitted",
        "turn": session["turn"],
        "field_key": key,
        "attempt_number": current_attempt,
        "answer_quality": quality,
    })
    return get_intake_state(session_id)


def apply_analysis_turn(
    session_id: str,
    *,
    extraction: dict[str, Any],
    decision: dict[str, Any],
    question: str,
    attempt_number: int,
    recommended_exams: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    session = intake_sessions.get(session_id)
    updates = extraction.get("field_updates") or []
    session["field_states"] = merge_field_updates(session["field_states"], updates, session["turn"])
    session["execution"] = calculate_execution(session["field_states"], session["context"])
    session["conflicts"].extend(extraction.get("conflicts") or [])
    session["safety_alerts"] = list(dict.fromkeys(session["safety_alerts"] + (extraction.get("red_flags") or [])))
    session["blocking_keys"] = decision.get("blocking_keys") or []
    session["audit"].append({
        "event": "analysis_applied",
        "turn": session["turn"],
        "decision": decision.get("reason"),
        "rule_version": RULE_VERSION,
    })

    if decision.get("stop"):
        reason = str(decision.get("reason") or "no_collectable_gap")
        session.update({
            "phase": "escalated" if reason == "red_flag_escalation" else "completed",
            "stop_reason": reason,
            "current_question": "",
            "current_field_key": "",
            "attempt_number": 0,
            "recommended_exams": recommended_exams or session["recommended_exams"],
        })
        session["report_markdown"] = generate_report(session)
    else:
        key = str(decision.get("next_field_key") or "")
        session.update({
            "phase": "follow_up",
            "stop_reason": None,
            "current_question": question or question_for_field(key, attempt_number),
            "current_field_key": key,
            "attempt_number": attempt_number,
        })
    return get_intake_state(session_id)


def generate_report(state: dict[str, Any]) -> str:
    rows = [
        "## 成人肥胖诊前资料",
        "",
        f"**开放描述：** {state.get('open_answer') or '未提供'}",
        "",
        "| 资料项目 | 已收集内容 |",
        "| --- | --- |",
    ]
    grouped: dict[str, dict[str, Any]] = {}
    for definition in FIELD_DEFINITIONS:
        field = state.get("field_states", {}).get(definition.key, {})
        group = grouped.setdefault(definition.group, {"evidence": [], "statuses": []})
        group["statuses"].append(field.get("status", "not_asked"))
        for evidence in field.get("evidence") or []:
            if evidence not in group["evidence"]:
                group["evidence"].append(evidence)
    for group_name, group in grouped.items():
        if group["evidence"]:
            detail = "；".join(group["evidence"])
        elif group["statuses"] and all(status == "not_applicable" for status in group["statuses"]):
            detail = "不适用"
        else:
            detail = "待诊中确认"
        rows.append(f"| {group_name} | {detail} |")
    if state.get("follow_up_answers"):
        rows.extend(["", "### 完整问答记录"])
        for index, item in enumerate(state["follow_up_answers"], start=1):
            rows.append(f"{index}. 问：{item['question']}  答：{item['answer']}")
    rows.extend([
        "",
        "**舌象与脉象：** 舌照可选；脉象待医生诊中采集。",
        "",
        "本档案仅用于诊前资料整理和检查准备，不能替代医生诊断或治疗。",
    ])
    return "\n".join(rows)


def _answer_is_unavailable(answer: str) -> bool:
    compact = answer.replace(" ", "")
    if len(compact) > 24:
        return False
    return any(marker in compact for marker in UNAVAILABLE_MARKERS)


def _build_summary(session: dict[str, Any]) -> dict[str, str]:
    summary = {}
    if session.get("open_answer"):
        summary["开放描述"] = session["open_answer"]
    confirmed = sum(1 for item in session["field_states"].values() if item["status"] == "confirmed")
    if confirmed:
        summary["已明确字段"] = f"{confirmed} 项"
    return summary


def _build_progress(session: dict[str, Any]) -> dict[str, Any]:
    phase = session["phase"]
    percent = {"open_intake": 0, "processing": 30, "follow_up": 55, "completed": 100, "escalated": 100}[phase]
    return {"answered": len(session["follow_up_answers"]) + (1 if session.get("open_answer") else 0), "total": None, "percent": percent}


def _build_stages(session: dict[str, Any]) -> list[dict[str, str]]:
    phase = session["phase"]
    return [
        {"id": "open", "label": "开放描述", "status": "completed" if session.get("open_answer") else "current"},
        {"id": "follow_up", "label": "补充问诊", "status": "current" if phase in {"processing", "follow_up"} else ("completed" if phase in {"completed", "escalated"} else "pending")},
        {"id": "result", "label": "诊前档案", "status": "current" if phase in {"completed", "escalated"} else "pending"},
    ]


def _assistant_note(session: dict[str, Any]) -> str:
    if session["phase"] == "open_intake":
        return "您可以按自己的话描述，不需要使用医学术语。"
    if session["phase"] in {"processing", "follow_up"}:
        return "我会根据您已经说过的内容，每次只补充确认一个重点。"
    return "本次诊前资料已整理，剩余信息请由医生诊中确认。"


# 旧接口兼容层：保留导入能力，患者新流程不再调用固定选项题。
def submit_intake_answer(session_id: str, question_id: str, option_id: str, note: str = "") -> dict[str, Any]:
    answer = note.strip() or option_id.strip()
    return submit_open_answer(session_id, answer)


def move_intake(session_id: str, direction: str) -> dict[str, Any]:
    if direction not in {"prev", "next"}:
        raise ValueError("移动方向只能是 prev 或 next")
    return get_intake_state(session_id)


def complete_intake_session(session_id: str) -> dict[str, Any]:
    session = intake_sessions.get(session_id)
    session["phase"] = "completed"
    session["stop_reason"] = session.get("stop_reason") or "manual_completion"
    session["report_markdown"] = generate_report(session)
    return get_intake_state(session_id)
