from __future__ import annotations

from typing import Any

from intake_execution import evaluate_patient_readiness
from obesity_intake_schema import FIELD_DEFINITIONS


STOP_REASON_LABELS = {
    "core_information_ready": "核心诊前信息已经完整，可以停止在线追问",
    "threshold_reached": "各信息层达到设定完整度阈值",
    "red_flag_escalation": "发现危险信号，停止常规追问并建议优先就医",
    "patient_unavailable": "患者暂时无法继续提供信息，转由医生面诊补充",
    "safety_limit": "达到保护性追问上限",
    "duplicate_gap": "剩余缺口与已问内容重复",
    "no_collectable_gap": "剩余信息不适合在线继续采集",
    "ai_unavailable": "智能整理暂不可用，已保护性结束",
    "manual_completion": "人工确认结束本次问诊",
    "manual_incomplete": "资料未完整，已保存供医生补充",
    "threshold_recheck_incomplete": "重新校验后仍有核心信息缺口",
}

EVENT_LABELS = {
    "session_created": "创建问诊",
    "baseline_confirmed": "确认基础测量",
    "question_selected": "选择下一项追问",
    "answer_recorded": "记录患者回答",
    "session_completed": "结束在线追问",
    "session_archived": "归档问诊",
}


def build_decision_explanation(state: dict[str, Any]) -> dict[str, Any]:
    definitions = {item.key: item for item in FIELD_DEFINITIONS}
    field_states = state.get("field_states") or {}
    readiness = evaluate_patient_readiness(field_states, state.get("context") or {})
    core_keys = readiness["core_field_keys"]
    safety_keys = [key for key in core_keys if definitions[key].layer == "safety"]

    def _has_unresolved_conflict(key: str) -> bool:
        return any(
            isinstance(conflict, dict) and not conflict.get("resolved", False)
            for conflict in (field_states.get(key) or {}).get("conflicts") or []
        )

    def _is_complete(key: str) -> bool:
        field = field_states.get(key) or {}
        return field.get("status") in {"confirmed", "not_applicable"} and not _has_unresolved_conflict(key)

    completed = sum(
        1 for key in core_keys if _is_complete(key)
    )
    safety_completed = sum(1 for key in safety_keys if _is_complete(key))
    core_conflicts = sum(
        1 for key in core_keys
        for conflict in (field_states.get(key) or {}).get("conflicts") or []
        if isinstance(conflict, dict) and not conflict.get("resolved", False)
    )
    selected_key = str(state.get("current_field_key") or "")
    definition = definitions.get(selected_key)
    selected_state = field_states.get(selected_key) or {}
    selected_field = None
    if selected_key:
        selected_field = {
            "key": selected_key,
            "label": definition.group if definition else selected_key,
            "question": definition.question if definition else state.get("current_question", ""),
            "status": selected_state.get("status", "not_asked"),
            "priority": definition.priority if definition else None,
            "attempts": selected_state.get("attempts", state.get("attempt_number", 0)),
            "source": definition.source if definition else "",
            "reason": "该项属于尚未确认的核心信息" if selected_key in core_keys else "按优先级补充诊前信息",
        }
    phase = str(state.get("phase") or "open_intake")
    should_stop = phase in {"completed", "incomplete", "escalated"}
    if phase == "escalated":
        readiness_status = "escalated"
    elif phase == "incomplete" or (phase == "completed" and not readiness["can_complete"]):
        readiness_status = "needs_doctor"
    else:
        readiness_status = "ready" if readiness["can_complete"] else "collecting"
    stop_reason = str(state.get("stop_reason") or "")
    if should_stop:
        reason = STOP_REASON_LABELS.get(stop_reason, "本次在线追问已经结束")
    elif readiness["blocking_keys"]:
        reason = "核心信息尚未完整，需要继续追问"
    else:
        reason = "核心信息已完整，系统将在本轮后结束追问"
    timeline = [
        {
            "event": item.get("event", "state_event"),
            "label": EVENT_LABELS.get(item.get("event"), "问诊状态更新"),
            "turn": item.get("turn"),
            "field_key": item.get("field_key"),
        }
        for item in (state.get("audit") or [])
    ]
    return {
        "status": "stop" if should_stop else "continue",
        "core_completed": completed,
        "core_total": len(core_keys),
        "blocking_fields": list(readiness["blocking_keys"]),
        "readiness": {
            "status": readiness_status,
            "baseline_ready": bool((state.get("context") or {}).get("baseline_confirmed")),
            "core": {"completed": completed, "total": len(core_keys)},
            "safety": {"completed": safety_completed, "total": len(safety_keys)},
            "core_conflicts": core_conflicts,
            "blocking_keys": list(readiness["blocking_keys"]),
            "optional_keys": list(readiness["doctor_follow_up_keys"]),
        },
        "selected_field": selected_field,
        "stop": {"should_stop": should_stop, "reason": reason, "code": stop_reason or None},
        "timeline": timeline,
    }
