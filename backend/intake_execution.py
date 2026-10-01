from __future__ import annotations

from copy import deepcopy
from typing import Any

from obesity_intake_schema import FIELD_DEFINITIONS, RULE_VERSION, get_applicable_fields


STATUS_COEFFICIENTS = {
    "confirmed": 1.0,
    "partial": 0.5,
    "not_asked": 0.0,
    "unavailable": 0.0,
}

NORMAL_THRESHOLDS = {"risk": 80.0, "tcm": 70.0, "safety": 100.0}

# Patient-side completion is intentionally narrower than the doctor-facing
# execution score: it covers the minimum safe and useful pre-visit dataset.
PATIENT_CORE_FIELD_KEYS = frozenset({
    "weight_change",
    "onset_course",
    "related_factors",
    "previous_weight_management",
    "appetite_thirst",
    "stool_urine",
    "sleep_emotion",
    "fatigue_activity",
    "diet_pattern",
    "exercise",
    "sleep_schedule",
    # One combined pre-visit question represented by glucose_tests covers
    # whether recent metabolic/liver/kidney/thyroid results are available.
    "glucose_tests",
    "allergies",
    "medications",
    "important_history",
    "red_flags",
    "pregnancy",
})

LEGACY_METABOLIC_KEY = "metabolic_tests"


def _blank_state(status: str = "not_asked") -> dict[str, Any]:
    return {
        "status": status,
        "evidence": [],
        "confidence": 0.0,
        "attempts": 0,
        "conflicts": [],
        "audit": [],
    }


def blank_field_states(context: dict[str, object] | None = None) -> dict[str, dict[str, Any]]:
    applicable_keys = {item.key for item in get_applicable_fields(context or {})}
    return {
        item.key: _blank_state("not_asked" if item.key in applicable_keys else "not_applicable")
        for item in FIELD_DEFINITIONS
    }


def migrate_field_states(
    current: dict[str, dict[str, Any]],
    context: dict[str, object] | None = None,
) -> dict[str, dict[str, Any]]:
    result = deepcopy(current)
    applicable_keys = {item.key for item in get_applicable_fields(context or {})}
    for definition in FIELD_DEFINITIONS:
        if definition.key not in result:
            status = "not_asked" if definition.key in applicable_keys else "not_applicable"
            result[definition.key] = _blank_state(status)
        elif definition.key not in applicable_keys:
            result[definition.key]["status"] = "not_applicable"
        elif context is not None and result[definition.key].get("status") == "not_applicable":
            field = result[definition.key]
            has_history = any(field.get(key) for key in ("evidence", "conflicts", "audit"))
            field["status"] = "partial" if has_history else "not_asked"
    return result


def merge_field_updates(
    current: dict[str, dict[str, Any]],
    updates: list[dict[str, Any]],
    source_turn: int,
) -> dict[str, dict[str, Any]]:
    result = migrate_field_states(current)
    known_keys = {item.key for item in FIELD_DEFINITIONS}
    for update in updates:
        key = str(update.get("field_key", "")).strip()
        if key == LEGACY_METABOLIC_KEY:
            result.setdefault(key, _blank_state())
            target_keys = (key,)
        elif key in known_keys:
            target_keys = (key,)
        else:
            continue
        status = str(update.get("status", "partial")).strip().lower()
        if status not in STATUS_COEFFICIENTS:
            status = "partial"
        evidence = str(update.get("evidence", "")).strip()
        confidence_value = update.get("confidence", 0.0)
        try:
            confidence = max(0.0, min(1.0, float(confidence_value)))
        except (TypeError, ValueError):
            confidence = 0.0

        has_conflict = bool(update.get("conflict"))
        for target_key in target_keys:
            field = result[target_key]
            if field.get("status") == "not_applicable":
                continue
            old_status = field.get("status", "not_asked")
            if evidence and evidence not in field["evidence"]:
                field["evidence"].append(evidence)
            target_status = "partial" if has_conflict else status
            if has_conflict:
                field["conflicts"].append({
                    "turn": source_turn,
                    "evidence": evidence,
                    "resolved": False,
                })
            elif target_status == "confirmed":
                for conflict in field["conflicts"]:
                    if isinstance(conflict, dict) and not conflict.get("resolved", False):
                        conflict.update({"resolved": True, "resolved_turn": source_turn})
            field["status"] = target_status
            field["confidence"] = confidence
            field["audit"].append({
                "turn": source_turn,
                "from_status": old_status,
                "to_status": target_status,
                "evidence": evidence,
                "confidence": confidence,
            })
    return result


def calculate_execution(
    field_states: dict[str, dict[str, Any]],
    context: dict[str, object] | None = None,
) -> dict[str, Any]:
    patient_context = context or {}
    applicable = get_applicable_fields(patient_context)
    raw_points: dict[str, float] = {}
    section_raw = {"differentiation": 0.0, "safety": 0.0}
    section_max = {"differentiation": 0.0, "safety": 0.0}
    layer_raw = {"risk": 0.0, "tcm": 0.0, "safety": 0.0}
    layer_max = {"risk": 0.0, "tcm": 0.0, "safety": 0.0}

    for definition in applicable:
        state = field_states.get(definition.key) or {"status": "not_asked"}
        coefficient = STATUS_COEFFICIENTS.get(state.get("status"), 0.0)
        points = round(definition.weight * coefficient, 2)
        raw_points[definition.key] = points
        section_raw[definition.section] += points
        section_max[definition.section] += definition.weight
        optional_unavailable = (
            state.get("status") == "unavailable"
            and int(state.get("attempts") or 0) >= definition.max_attempts
            and not definition.hard_required
            and definition.priority > 5
        )
        if definition.layer in layer_raw and not optional_unavailable:
            layer_raw[definition.layer] += points
            layer_max[definition.layer] += definition.weight

    differentiation = _normalized_score(section_raw["differentiation"], section_max["differentiation"], 70.0)
    legacy_safety = _normalized_score(section_raw["safety"], section_max["safety"], 30.0)
    scores = {
        layer: 100.0 if layer_max[layer] <= 0 else _normalized_score(layer_raw[layer], layer_max[layer], 100.0)
        for layer in layer_raw
    }
    baseline_ready = bool(patient_context.get("baseline_confirmed"))
    blocking_keys = []
    if not baseline_ready:
        blocking_keys.append("baseline")
    for layer, threshold in NORMAL_THRESHOLDS.items():
        if scores[layer] < threshold:
            blocking_keys.append(layer)
    return {
        "baseline_ready": baseline_ready,
        "risk_score": scores["risk"],
        "tcm_score": scores["tcm"],
        "safety_score": scores["safety"],
        "total_score": round(differentiation + legacy_safety, 1),
        "differentiation_score": differentiation,
        "blocking_keys": blocking_keys,
        "raw_points": raw_points,
        "section_raw": {key: round(value, 2) for key, value in section_raw.items()},
        "section_max": {key: round(value, 2) for key, value in section_max.items()},
        "layer_raw": {key: round(value, 2) for key, value in layer_raw.items()},
        "layer_max": {key: round(value, 2) for key, value in layer_max.items()},
        "rule_version": RULE_VERSION,
    }


def _normalized_score(raw: float, maximum: float, target: float) -> float:
    if maximum <= 0:
        return 0.0
    return round(raw / maximum * target, 1)


def evaluate_threshold(
    execution: dict[str, Any],
    field_states: dict[str, dict[str, Any]],
    context: dict[str, object] | None = None,
) -> dict[str, Any]:
    applicable = get_applicable_fields(context or {})
    blocking_keys = list(execution.get("blocking_keys") or [])
    for definition in applicable:
        state = field_states.get(definition.key) or {}
        status = state.get("status", "not_asked")
        if (definition.hard_required or definition.priority <= 5) and status not in {"confirmed", "not_applicable"}:
            blocking_keys.append(definition.key)
        if any(
            not conflict.get("resolved", False)
            for conflict in state.get("conflicts") or []
            if isinstance(conflict, dict)
        ):
            blocking_keys.append(definition.key)

    score_ok = (
        bool(execution.get("baseline_ready"))
        and execution.get("risk_score", 0) >= NORMAL_THRESHOLDS["risk"]
        and execution.get("tcm_score", 0) >= NORMAL_THRESHOLDS["tcm"]
        and execution.get("safety_score", 0) >= NORMAL_THRESHOLDS["safety"]
    )
    return {
        "can_complete": score_ok and not blocking_keys,
        "blocking_keys": list(dict.fromkeys(blocking_keys)),
        "execution": execution,
        "thresholds": dict(NORMAL_THRESHOLDS),
    }


def evaluate_patient_readiness(
    field_states: dict[str, dict[str, Any]],
    context: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Decide whether a patient has supplied the core pre-visit dataset.

    The detailed execution score remains available to doctors, but optional
    details should not keep a patient in an unbounded online questionnaire.
    """
    patient_context = context or {}
    applicable = get_applicable_fields(patient_context)
    core_definitions = [
        definition for definition in applicable
        if definition.key in PATIENT_CORE_FIELD_KEYS
    ]
    blocking_keys = []
    if not patient_context.get("baseline_confirmed"):
        blocking_keys.append("baseline")

    for definition in core_definitions:
        state = field_states.get(definition.key) or {}
        status = state.get("status", "not_asked")
        if status not in {"confirmed", "not_applicable"}:
            blocking_keys.append(definition.key)
        if any(
            not conflict.get("resolved", False)
            for conflict in state.get("conflicts") or []
            if isinstance(conflict, dict)
        ):
            blocking_keys.append(definition.key)

    doctor_follow_up_keys = [
        definition.key for definition in applicable
        if definition.key not in PATIENT_CORE_FIELD_KEYS
        and (field_states.get(definition.key) or {}).get("status") not in {"confirmed", "not_applicable"}
    ]
    return {
        "can_complete": not blocking_keys,
        "blocking_keys": list(dict.fromkeys(blocking_keys)),
        "core_field_keys": [definition.key for definition in core_definitions],
        "doctor_follow_up_keys": doctor_follow_up_keys,
    }
