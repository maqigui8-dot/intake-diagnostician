from __future__ import annotations

from typing import Any

from obesity_intake_schema import FIELD_DEFINITIONS, RULE_VERSION


PUBLIC_STOP_REASONS = {
    "threshold_reached": "本次诊前资料已整理完成。",
    "red_flag_escalation": "您描述的情况需要优先由医生线下评估，请及时就医。",
    "patient_unavailable": "部分信息暂时无法确认，请在诊中向医生补充。",
    "safety_limit": "历史问诊已保护性结束，剩余信息请在诊中补充。",
    "duplicate_gap": "当前能在线确认的信息已整理，剩余内容请在诊中补充。",
    "no_collectable_gap": "当前能在线确认的信息已整理，剩余内容请在诊中补充。",
    "ai_unavailable": "智能整理暂时不可用，已保存的安全信息可供医生查看。",
    "manual_completion": "本次诊前资料已整理完成。",
    "manual_incomplete": "当前资料尚未达到完整条件，已保存供医生诊中补充。",
    "threshold_recheck_incomplete": "当前资料尚未满足现行完整条件，可继续补充后再次确认。",
}


def build_patient_state(internal_state: dict[str, Any]) -> dict[str, Any]:
    history = [
        {
            "question": item.get("question", ""),
            "answer": item.get("answer", ""),
            "attempt_number": item.get("attempt_number", 1),
        }
        for item in internal_state.get("follow_up_answers") or []
    ]
    phase = internal_state.get("phase", "open_intake")
    return {
        "session_id": internal_state.get("session_id", ""),
        "phase": phase,
        "open_question": internal_state.get("open_question", ""),
        "open_answer": internal_state.get("open_answer", ""),
        "follow_up_answers": history,
        "follow_up_count": len(history),
        "next_question": internal_state.get("current_question", "") if phase == "follow_up" else "",
        "attempt_number": internal_state.get("attempt_number", 0) if phase == "follow_up" else 0,
        "safety_alerts": list(internal_state.get("safety_alerts") or []),
        "report_markdown": internal_state.get("report_markdown"),
        "recommended_exams": list(internal_state.get("recommended_exams") or []) if phase in {"completed", "escalated"} else [],
        "stop_reason_public": PUBLIC_STOP_REASONS.get(internal_state.get("stop_reason"), ""),
        "is_complete": phase == "completed",
    }


def build_doctor_summary(internal_state: dict[str, Any]) -> dict[str, Any]:
    definitions = {item.key: item for item in FIELD_DEFINITIONS}
    groups = {"confirmed": [], "partial": [], "unavailable": [], "not_asked": [], "not_applicable": []}
    safety_fields = []
    legacy_fields = {}
    for key, field in (internal_state.get("field_states") or {}).items():
        definition = definitions.get(key)
        if not definition:
            if key == "metabolic_tests":
                legacy_fields[key] = {
                    "status": field.get("status", "not_asked"),
                    "evidence": list(field.get("evidence") or []),
                    "confidence": field.get("confidence", 0.0),
                    "attempts": field.get("attempts", 0),
                    "conflicts": list(field.get("conflicts") or []),
                    "audit": list(field.get("audit") or []),
                }
            continue
        item = {
            "field_key": key,
            "group": definition.group,
            "section": definition.section,
            "status": field.get("status", "not_asked"),
            "weight": definition.weight,
            "evidence": list(field.get("evidence") or []),
            "confidence": field.get("confidence", 0.0),
            "attempts": field.get("attempts", 0),
            "conflicts": list(field.get("conflicts") or []),
            "source": definition.source,
        }
        groups.setdefault(item["status"], []).append(item)
        if definition.section == "safety":
            safety_fields.append(item)

    execution = dict(internal_state.get("execution") or {})
    return {
        "access_scope": "prototype_doctor_view",
        "session_id": internal_state.get("session_id", ""),
        "phase": internal_state.get("phase", "open_intake"),
        "execution": execution,
        "threshold_reached": internal_state.get("stop_reason") == "threshold_reached",
        "stop_reason": internal_state.get("stop_reason"),
        "rule_version": execution.get("rule_version", RULE_VERSION),
        "field_groups": groups,
        "legacy_fields": legacy_fields,
        "safety_fields": safety_fields,
        "blocking_keys": list(internal_state.get("blocking_keys") or []),
        "conflicts": list(internal_state.get("conflicts") or []),
        "safety_alerts": list(internal_state.get("safety_alerts") or []),
        "open_answer": internal_state.get("open_answer", ""),
        "follow_up_answers": list(internal_state.get("follow_up_answers") or []),
        "audit": list(internal_state.get("audit") or []),
        "recommended_exams": list(internal_state.get("recommended_exams") or []),
    }
