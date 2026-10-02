from __future__ import annotations

from typing import Any

from intake_execution import NORMAL_THRESHOLDS, evaluate_patient_readiness
from decision_explanation import build_decision_explanation
from intake_question_policy import select_next_field
from intake_flow import PATIENT_REVIEW_FIELD_KEYS
from obesity_intake_schema import FIELD_DEFINITIONS, RULE_VERSION


PUBLIC_STOP_REASONS = {
    "core_information_ready": "本次核心诊前资料已整理完成，请核对后保存。",
    "threshold_reached": "本次诊前资料已整理完成。",
    "red_flag_escalation": "您描述的情况需要优先由医生线下评估，请及时就医。",
    "patient_unavailable": "部分信息暂时无法确认，本次回答已保留为可补充草稿。",
    "safety_limit": "在线追问已结束，未确认信息仍保留在草稿中。",
    "duplicate_gap": "当前能在线确认的信息已整理，未确认项可在下方自行补充。",
    "no_collectable_gap": "当前能在线确认的信息已整理，未确认项可在下方自行补充。",
    "ai_unavailable": "智能整理暂时不可用，本次在线追问已结束；已提供的安全信息仍保留在本次问诊中。",
    "manual_completion": "本次诊前资料已整理完成。",
    "manual_incomplete": "当前资料尚未达到完整条件，未列入已完成档案。",
    "threshold_recheck_incomplete": "重新校验后，当前资料仍有关键项目未确认。",
}


SECTION_BASELINE = "基础测量与肥胖范围"
SECTION_COURSE = "肥胖病程与可能病因"
SECTION_DISEASE = "相关疾病风险"
SECTION_LIFESTYLE = "生活方式与心理情况"
SECTION_TCM = "中医诊前资料"
SECTION_PENDING = "待医生确认"

SECTION_ORDER = (
    SECTION_BASELINE,
    SECTION_COURSE,
    SECTION_DISEASE,
    SECTION_LIFESTYLE,
    SECTION_TCM,
    SECTION_PENDING,
)

DOCTOR_CONFIRMATION_HINT = (
    "成人BMI规则仅适用于18岁及以上；患者端仅显示“达到成人肥胖范围，待医生确认”，"
    "不直接确诊、不输出患病概率、不自动辨证或开方。"
)


def _section_for_definition(definition: Any) -> str:
    if definition.layer == "baseline":
        return SECTION_BASELINE
    if definition.layer == "safety":
        return SECTION_PENDING
    if definition.layer == "tcm":
        return SECTION_TCM
    if definition.group == "近期检查":
        return SECTION_DISEASE
    if definition.group == "生活方式与心理因素":
        return SECTION_LIFESTYLE
    return SECTION_COURSE


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
    readiness = build_decision_explanation(internal_state)["readiness"]
    core_readiness = evaluate_patient_readiness(
        internal_state.get("field_states") or {}, internal_state.get("context") or {},
    )
    core_keys = core_readiness["core_field_keys"]
    blocking_keys = set(core_readiness["blocking_keys"])
    field_definitions = {definition.key: definition for definition in FIELD_DEFINITIONS}
    blocking_fields = [
        {
            "field_key": key,
            "label": field_definitions[key].question,
            "status": (internal_state.get("field_states") or {}).get(key, {}).get("status", "not_asked"),
            "value": "；".join((internal_state.get("field_states") or {}).get(key, {}).get("evidence") or []),
        }
        for key in core_readiness["blocking_keys"]
        if key in field_definitions
    ]
    unavailable_count = sum(
        (internal_state.get("field_states") or {}).get(key, {}).get("status") == "unavailable"
        for key in core_keys
    )
    can_continue = phase == "incomplete" and bool(select_next_field(
        internal_state.get("field_states") or {},
        internal_state.get("follow_up_answers") or [],
        internal_state.get("context") or {},
        field_keys=set(readiness["blocking_keys"]),
    ))
    review_fields = [
        {
            "field_key": definition.key,
            "label": definition.question if phase == "incomplete" and definition.key in blocking_keys else definition.group,
            "value": "；".join((internal_state.get("field_states") or {}).get(definition.key, {}).get("evidence") or []),
            "status": (internal_state.get("field_states") or {}).get(definition.key, {}).get("status", "not_asked"),
        }
        for definition in FIELD_DEFINITIONS
        if definition.key in PATIENT_REVIEW_FIELD_KEYS or (
            phase == "incomplete" and definition.key in blocking_keys
        )
    ]
    return {
        "session_id": internal_state.get("session_id", ""),
        "phase": phase,
        "baseline": internal_state.get("baseline"),
        "bmi_assessment": internal_state.get("bmi_assessment"),
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
        "can_continue": can_continue,
        "blocking_fields": blocking_fields if phase == "incomplete" else [],
        "review_fields": review_fields if phase in {"completed", "incomplete"} else [],
        "progress": {
            "core_completed": readiness["core"]["completed"],
            "core_total": readiness["core"]["total"],
            "remaining_count": readiness["core"]["total"] - readiness["core"]["completed"],
            "pending_count": readiness["core"]["total"] - readiness["core"]["completed"] - unavailable_count,
            "unavailable_count": unavailable_count,
            "ready": readiness["status"] == "ready",
        },
    }


def build_doctor_summary(internal_state: dict[str, Any]) -> dict[str, Any]:
    definitions = {item.key: item for item in FIELD_DEFINITIONS}
    groups: dict[str, list[dict[str, Any]]] = {section: [] for section in SECTION_ORDER}
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
            "layer": definition.layer,
            "status": field.get("status", "not_asked"),
            "weight": definition.weight,
            "evidence": list(field.get("evidence") or []),
            "confidence": field.get("confidence", 0.0),
            "attempts": field.get("attempts", 0),
            "conflicts": list(field.get("conflicts") or []),
            "source": definition.source,
        }
        groups[_section_for_definition(definition)].append(item)
        if definition.layer == "safety":
            safety_fields.append(item)

    execution = dict(internal_state.get("execution") or {})
    baseline = internal_state.get("baseline") or {}
    bmi_assessment = internal_state.get("bmi_assessment") or {}

    baseline_summary = {
        "age": baseline.get("age"),
        "sex": baseline.get("sex"),
        "height_cm": baseline.get("height_cm"),
        "weight_kg": baseline.get("weight_kg"),
        "waist_cm": baseline.get("waist_cm"),
        "hip_cm": baseline.get("hip_cm"),
        "measured_at": baseline.get("measured_at"),
        "bmi": bmi_assessment.get("bmi"),
        "bmi_grade": bmi_assessment.get("bmi_grade"),
        "central_obesity": bmi_assessment.get("central_obesity"),
        "diagnosis_copy": bmi_assessment.get("diagnosis_copy"),
        "rule_hint": DOCTOR_CONFIRMATION_HINT,
    }

    layer_raw = execution.get("layer_raw") or {}
    layer_max = execution.get("layer_max") or {}

    def _scored_layer(key: str, label: str) -> dict[str, Any]:
        return {
            "key": key,
            "label": label,
            "score": execution.get(f"{key}_score", 0.0),
            "threshold": NORMAL_THRESHOLDS.get(key),
            "raw": layer_raw.get(key),
            "max": layer_max.get(key),
        }

    layer_execution = {
        "baseline": {
            "key": "baseline",
            "label": "基础测量",
            "ready": bool(execution.get("baseline_ready")),
            "score": 100.0 if execution.get("baseline_ready") else 0.0,
            "threshold": None,
            "raw": None,
            "max": None,
        },
        "risk": _scored_layer("risk", "病因与风险"),
        "tcm": _scored_layer("tcm", "中医诊前"),
        "safety": _scored_layer("safety", "安全"),
    }

    decision_explanation = build_decision_explanation(internal_state)
    return {
        "access_scope": "prototype_doctor_view",
        "session_id": internal_state.get("session_id", ""),
        "phase": internal_state.get("phase", "open_intake"),
        "execution": execution,
        "baseline_assessment": baseline_summary,
        "layer_execution": layer_execution,
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
        "decision_explanation": decision_explanation,
        "readiness_summary": decision_explanation["readiness"],
    }
