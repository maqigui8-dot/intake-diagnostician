from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from intake_execution import (
    PATIENT_CORE_FIELD_KEYS,
    blank_field_states,
    calculate_execution,
    evaluate_patient_readiness,
    merge_field_updates,
    migrate_field_states,
)
from intake_question_policy import is_clarification_request, question_for_field
from exam_recommendations import build_recommended_exams
from obesity_diagnosis import validate_baseline
from obesity_intake_schema import FIELD_DEFINITIONS, RULE_VERSION


OPEN_QUESTION = "这次您最想改善的体重或身体方面的困扰是什么？可以说说什么时候开始，以及最近有什么变化。"
UNAVAILABLE_MARKERS = ("不知道", "不清楚", "不记得", "说不清", "不方便", "不想说", "拒绝")
PROTECTIVE_STOP_REASONS = {
    "patient_unavailable",
    "duplicate_gap",
    "no_collectable_gap",
    "ai_unavailable",
}
PATIENT_REVIEW_FIELD_KEYS = frozenset({
    "main_goal", "onset_course", "allergies", "medications", "important_history",
})


def _normalize_resident_session(session: dict[str, Any]) -> None:
    context = session.setdefault("context", {})
    if "baseline_confirmed" not in context:
        context["baseline_confirmed"] = bool(session.get("baseline_confirmed"))
    baseline = session.get("baseline")
    if isinstance(baseline, dict) and baseline.get("sex") in {"male", "female"}:
        context["pregnancy_applicable"] = baseline["sex"] == "female"
    session["field_states"] = migrate_field_states(session.get("field_states") or {}, context)
    session["execution"] = calculate_execution(session["field_states"], context)
    readiness = evaluate_patient_readiness(session["field_states"], context)
    session["blocking_keys"] = readiness["blocking_keys"]
    if session.get("phase") == "completed" and session.get("stop_reason") in PROTECTIVE_STOP_REASONS:
        session["phase"] = "incomplete"
    elif (
        session.get("phase") == "completed"
        and not readiness["can_complete"]
    ):
        stop_reason = "manual_incomplete" if session.get("stop_reason") == "manual_completion" else "threshold_recheck_incomplete"
        session.update({"phase": "incomplete", "stop_reason": stop_reason})


class IntakeSessionStore:
    def __init__(self, repository=None):
        self._sessions: dict[str, dict[str, Any]] = {}
        self._repository = repository

    def configure(self, repository=None):
        self._repository = repository
        self._sessions.clear()

    def clear(self):
        if self._repository is not None:
            self._repository.clear()
        self._sessions.clear()

    def get(self, session_id: str, patient_id: str | None = None) -> dict[str, Any]:
        if self._repository is not None:
            owner = patient_id or self._repository.get_session_owner(session_id) or "demo-zhang"
            session = self._repository.get_or_create_session(session_id, owner)
            _normalize_resident_session(session)
            return session
        if session_id not in self._sessions:
            context: dict[str, object] = {
                "baseline_confirmed": False,
                "pregnancy_applicable": True,
            }
            field_states = blank_field_states(context)
            self._sessions[session_id] = {
                "session_id": session_id,
                "phase": "baseline_collection",
                "context": context,
                "open_question": OPEN_QUESTION,
                "baseline": None,
                "bmi_assessment": None,
                "baseline_confirmed": False,
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
        session = self._sessions[session_id]
        _normalize_resident_session(session)
        return session

    def save(self, session: dict[str, Any]) -> dict[str, Any]:
        if self._repository is not None:
            return self._repository.save_session_state(
                session, expected_version=session.get("version")
            )
        self._sessions[str(session["session_id"])] = session
        return session


intake_sessions = IntakeSessionStore()


def configure_intake_repository(repository=None) -> None:
    intake_sessions.configure(repository)


def create_intake_session(patient_id: str, session_id: str) -> dict[str, Any]:
    return get_intake_state(session_id, patient_id)


def get_intake_state(session_id: str, patient_id: str | None = None) -> dict[str, Any]:
    session = intake_sessions.get(session_id, patient_id)
    state = deepcopy(session)
    state.update({
        "follow_up_count": len(session["follow_up_answers"]),
        "is_complete": session["phase"] == "completed",
        "summary": _build_summary(session),
        "answers": {},
        "progress": _build_progress(session),
        "stages": _build_stages(session),
        "assistant_note": _assistant_note(session),
    })
    return state


def get_internal_intake_state(session_id: str, patient_id: str | None = None) -> dict[str, Any]:
    return intake_sessions.get(session_id, patient_id)


def require_baseline_confirmation(session_id: str, patient_id: str | None = None) -> None:
    if not intake_sessions.get(session_id, patient_id)["baseline_confirmed"]:
        raise ValueError("请先完成基础测量并确认后，再继续问诊。")


def set_baseline(session_id: str, payload: dict[str, object], patient_id: str | None = None) -> dict[str, Any]:
    validated = validate_baseline(payload)
    session = intake_sessions.get(session_id, patient_id)
    session["baseline"] = {
        key: validated[key]
        for key in ("age", "sex", "height_cm", "weight_kg", "waist_cm", "hip_cm", "measured_at")
    }
    session["bmi_assessment"] = {
        key: validated[key]
        for key in ("bmi", "bmi_grade", "central_obesity")
    }
    if "diagnosis_copy" in validated:
        session["bmi_assessment"]["diagnosis_copy"] = validated["diagnosis_copy"]
    session["context"].update({
        "baseline_confirmed": True,
        "pregnancy_applicable": validated["sex"] == "female",
    })
    session["field_states"] = migrate_field_states(session["field_states"], session["context"])
    session["execution"] = calculate_execution(session["field_states"], session["context"])
    session.update({"baseline_confirmed": True, "phase": "open_intake"})
    session["audit"].append({
        "event": "baseline_confirmed",
        "turn": session["turn"],
        "rule_version": RULE_VERSION,
    })
    intake_sessions.save(session)
    return get_intake_state(session_id, patient_id)


def submit_open_answer(session_id: str, answer: str, patient_id: str | None = None) -> dict[str, Any]:
    require_baseline_confirmation(session_id, patient_id)
    clean_answer = answer.strip()
    if not clean_answer:
        raise ValueError("开放回答不能为空")
    session = intake_sessions.get(session_id, patient_id)
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
    intake_sessions.save(session)
    return get_intake_state(session_id, patient_id)


def submit_follow_up_answer(
    session_id: str,
    answer: str,
    legacy_answer: str | None = None,
    *,
    question_key: str = "",
    question_kind: str = "required",
    attempt_number: int | None = None,
) -> dict[str, Any]:
    require_baseline_confirmation(session_id)
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

    previous_attempts = sum(
        1
        for item in session["follow_up_answers"]
        if item.get("question_key") == key and item.get("answer_quality") != "clarification"
    )
    current_attempt = attempt_number or session.get("attempt_number") or (previous_attempts + 1)
    current_attempt = max(previous_attempts + 1, int(current_attempt))
    if current_attempt > 2:
        raise ValueError("该项信息已询问两次；本轮追问结束后仍可在草稿中补充")

    if is_clarification_request(clean_answer):
        quality = "clarification"
    elif _answer_is_unavailable(clean_answer):
        quality = "unavailable"
    else:
        quality = "provided"
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
    if field is not None and quality != "clarification":
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
    intake_sessions.save(session)
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
    require_baseline_confirmation(session_id)
    session = intake_sessions.get(session_id)
    updates = extraction.get("field_updates") or []
    session["field_states"] = merge_field_updates(session["field_states"], updates, session["turn"])
    session["execution"] = calculate_execution(session["field_states"], session["context"])
    readiness = evaluate_patient_readiness(session["field_states"], session["context"])
    session["conflicts"].extend(extraction.get("conflicts") or [])
    session["safety_alerts"] = list(dict.fromkeys(session["safety_alerts"] + (extraction.get("red_flags") or [])))
    session["blocking_keys"] = readiness["blocking_keys"]
    session["audit"].append({
        "event": "analysis_applied",
        "turn": session["turn"],
        "decision": decision.get("reason"),
        "rule_version": RULE_VERSION,
    })

    if decision.get("stop"):
        reason = str(decision.get("reason") or "no_collectable_gap")
        if reason == "red_flag_escalation":
            terminal_phase = "escalated"
        elif decision.get("complete") and readiness["can_complete"]:
            terminal_phase = "completed"
        else:
            terminal_phase = "incomplete"
        session.update({
            "phase": terminal_phase,
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
    intake_sessions.save(session)
    return get_intake_state(session_id)


def generate_report(state: dict[str, Any]) -> str:
    is_draft = state.get("phase") == "incomplete"
    rows = [
        "## 成人肥胖诊前资料草稿" if is_draft else "## 成人肥胖诊前资料",
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
            detail = "尚未提供"
        rows.append(f"| {group_name} | {detail} |")
    if state.get("patient_corrections"):
        rows.extend(["", "### 患者核对修正"])
        labels = {item.key: item.group for item in FIELD_DEFINITIONS}
        for item in state["patient_corrections"]:
            rows.append(
                f"- {labels.get(item['field_key'], item['field_key'])}："
                f"原记录“{item['previous'] or '未记录'}”，患者修正为“{item['updated']}”。"
            )
    if state.get("follow_up_answers"):
        rows.extend(["", "### 完整问答记录"])
        for index, item in enumerate(state["follow_up_answers"], start=1):
            rows.append(f"{index}. 问：{item['question']}  答：{item['answer']}")
    rows.extend([
        "",
        "**舌象与脉象：** 舌照可选；脉象不由本系统采集。",
        "",
        (
            "本草稿仍有未确认信息，仅用于继续整理诊前资料，不能替代医生诊断或治疗。"
            if is_draft else
            "本档案仅用于诊前资料整理和检查准备，不能替代医生诊断或治疗。"
        ),
    ])
    return "\n".join(rows)


def correct_patient_field(
    session_id: str, field_key: str, value: str, patient_id: str | None = None,
) -> dict[str, Any]:
    session = intake_sessions.get(session_id, patient_id)
    if session.get("phase") not in {"completed", "incomplete"}:
        raise ValueError("仅在问诊结束后可以核对并修正资料")
    readiness_before = evaluate_patient_readiness(session["field_states"], session["context"])
    draft_blocker = (
        session.get("phase") == "incomplete"
        and field_key in PATIENT_CORE_FIELD_KEYS
        and field_key in readiness_before["blocking_keys"]
    )
    if field_key not in PATIENT_REVIEW_FIELD_KEYS and not draft_blocker:
        raise ValueError("该项不可在此修改，请通过线下就医进一步确认")
    clean = " ".join(str(value or "").split())
    if not clean or len(clean) > 300:
        raise ValueError("修正内容须为 1 至 300 字")

    field = session["field_states"][field_key]
    previous = "；".join(field.get("evidence") or [])
    if previous == clean and not draft_blocker:
        return get_intake_state(session_id, patient_id)
    unavailable = _answer_is_unavailable(clean)
    added_red_flags: list[str] = []
    if draft_blocker and not unavailable:
        from skill_analysis import extract_local_follow_up_field, extract_local_red_flags

        correction_update = extract_local_follow_up_field(field_key, clean)
        if not correction_update or correction_update.get("status") != "confirmed":
            raise ValueError("补充内容未能回答当前资料项，请根据提示具体说明")
        if field_key == "red_flags":
            added_red_flags = extract_local_red_flags(clean)
            if session.get("safety_alerts") and not added_red_flags:
                raise ValueError("已有危险信号记录，不能通过此处的否定回答清除")
    session["turn"] += 1
    correction = {
        "field_key": field_key,
        "previous": previous,
        "updated": clean,
        "turn": session["turn"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    session.setdefault("patient_corrections", []).append(correction)
    field["evidence"] = [clean]
    field["status"] = "unavailable" if unavailable else "confirmed"
    field["confidence"] = 1.0 if not unavailable else 0.0
    if added_red_flags:
        session["safety_alerts"] = list(dict.fromkeys([
            *(session.get("safety_alerts") or []), *added_red_flags,
        ]))
    if not unavailable:
        for conflict in field.get("conflicts") or []:
            if isinstance(conflict, dict) and not conflict.get("resolved", False):
                conflict.update({"resolved": True, "resolved_turn": session["turn"]})
    field.setdefault("audit", []).append({
        "turn": session["turn"], "event": "patient_correction",
        "previous": previous, "updated": clean,
    })
    session["audit"].append({
        "event": "patient_field_corrected", "turn": session["turn"], "field_key": field_key,
    })
    session["execution"] = calculate_execution(session["field_states"], session["context"])
    readiness = evaluate_patient_readiness(session["field_states"], session["context"])
    session["blocking_keys"] = readiness["blocking_keys"]
    session["phase"] = "completed" if readiness["can_complete"] else "incomplete"
    session["stop_reason"] = "core_information_ready" if readiness["can_complete"] else "manual_incomplete"
    session["recommended_exams"] = (
        build_recommended_exams(session["field_states"], red_flags=session.get("safety_alerts") or [])
        if readiness["can_complete"] else []
    )
    session["report_markdown"] = generate_report(session)
    intake_sessions.save(session)
    return get_intake_state(session_id, patient_id)


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
    percent = {
        "baseline_collection": 0,
        "open_intake": 0,
        "processing": 30,
        "follow_up": 55,
        "completed": 100,
        "incomplete": 100,
        "escalated": 100,
    }[phase]
    return {"answered": len(session["follow_up_answers"]) + (1 if session.get("open_answer") else 0), "total": None, "percent": percent}


def _build_stages(session: dict[str, Any]) -> list[dict[str, str]]:
    phase = session["phase"]
    return [
        {"id": "open", "label": "开放描述", "status": "completed" if session.get("open_answer") else "current"},
        {"id": "follow_up", "label": "补充问诊", "status": "current" if phase in {"processing", "follow_up"} else ("completed" if phase in {"completed", "incomplete", "escalated"} else "pending")},
        {"id": "result", "label": "诊前档案", "status": "current" if phase in {"completed", "incomplete", "escalated"} else "pending"},
    ]


def _assistant_note(session: dict[str, Any]) -> str:
    if session["phase"] == "baseline_collection":
        return "请先完成年龄、性别、身高、体重和测量时间等基础测量。"
    if session["phase"] == "open_intake":
        return "您可以按自己的话描述，不需要使用医学术语。"
    if session["phase"] in {"processing", "follow_up"}:
        return "我会根据您已经说过的内容，每次只补充确认一个重点。"
    return "本次诊前资料已整理；如有未确认项，可在草稿中补充。"


# 旧接口兼容层：保留导入能力，患者新流程不再调用固定选项题。
def submit_intake_answer(session_id: str, question_id: str, option_id: str, note: str = "") -> dict[str, Any]:
    answer = note.strip() or option_id.strip()
    return submit_open_answer(session_id, answer)


def move_intake(session_id: str, direction: str) -> dict[str, Any]:
    if direction not in {"prev", "next"}:
        raise ValueError("移动方向只能是 prev 或 next")
    return get_intake_state(session_id)


def complete_intake_session(session_id: str) -> dict[str, Any]:
    require_baseline_confirmation(session_id)
    session = intake_sessions.get(session_id)
    session["execution"] = calculate_execution(session["field_states"], session["context"])
    readiness = evaluate_patient_readiness(session["field_states"], session["context"])
    session["blocking_keys"] = readiness["blocking_keys"]
    session["phase"] = "completed" if readiness["can_complete"] else "incomplete"
    session["stop_reason"] = "manual_completion" if readiness["can_complete"] else "manual_incomplete"
    session["report_markdown"] = generate_report(session)
    intake_sessions.save(session)
    return get_intake_state(session_id)
