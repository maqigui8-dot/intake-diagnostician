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

NORMAL_THRESHOLDS = {
    "total": 85.0,
    "differentiation": 55.0,
    "safety": 27.0,
}


def blank_field_states(context: dict[str, object] | None = None) -> dict[str, dict[str, Any]]:
    applicable_keys = {item.key for item in get_applicable_fields(context or {})}
    return {
        item.key: {
            "status": "not_asked" if item.key in applicable_keys else "not_applicable",
            "evidence": [],
            "confidence": 0.0,
            "attempts": 0,
            "conflicts": [],
            "audit": [],
        }
        for item in FIELD_DEFINITIONS
    }


def merge_field_updates(
    current: dict[str, dict[str, Any]],
    updates: list[dict[str, Any]],
    source_turn: int,
) -> dict[str, dict[str, Any]]:
    result = deepcopy(current)
    known_keys = {item.key for item in FIELD_DEFINITIONS}
    for update in updates:
        key = str(update.get("field_key", "")).strip()
        if key not in known_keys or result.get(key, {}).get("status") == "not_applicable":
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

        field = result[key]
        old_status = field.get("status", "not_asked")
        if evidence and evidence not in field["evidence"]:
            field["evidence"].append(evidence)

        has_conflict = bool(update.get("conflict"))
        if has_conflict:
            field["conflicts"].append({"turn": source_turn, "evidence": evidence})
            status = "partial"

        field["status"] = status
        field["confidence"] = confidence
        field["audit"].append({
            "turn": source_turn,
            "from_status": old_status,
            "to_status": status,
            "evidence": evidence,
            "confidence": confidence,
        })
    return result


def calculate_execution(
    field_states: dict[str, dict[str, Any]],
    context: dict[str, object] | None = None,
) -> dict[str, Any]:
    applicable = get_applicable_fields(context or {})
    raw_points: dict[str, float] = {}
    section_raw = {"differentiation": 0.0, "safety": 0.0}
    section_max = {"differentiation": 0.0, "safety": 0.0}

    for definition in applicable:
        state = field_states.get(definition.key, {"status": "not_asked"})
        coefficient = STATUS_COEFFICIENTS.get(state.get("status"), 0.0)
        points = round(definition.weight * coefficient, 2)
        raw_points[definition.key] = points
        section_raw[definition.section] += points
        section_max[definition.section] += definition.weight

    differentiation = _normalized_score(section_raw["differentiation"], section_max["differentiation"], 70.0)
    safety = _normalized_score(section_raw["safety"], section_max["safety"], 30.0)
    return {
        "total_score": round(differentiation + safety, 1),
        "differentiation_score": differentiation,
        "safety_score": safety,
        "raw_points": raw_points,
        "section_raw": {key: round(value, 2) for key, value in section_raw.items()},
        "section_max": {key: round(value, 2) for key, value in section_max.items()},
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
    blocking_keys = []
    for definition in applicable:
        status = field_states.get(definition.key, {}).get("status", "not_asked")
        if definition.hard_required and status in {"not_asked", "unavailable"}:
            blocking_keys.append(definition.key)
        elif definition.priority <= 5 and status == "not_asked":
            blocking_keys.append(definition.key)

    score_ok = (
        execution.get("total_score", 0) >= NORMAL_THRESHOLDS["total"]
        and execution.get("differentiation_score", 0) >= NORMAL_THRESHOLDS["differentiation"]
        and execution.get("safety_score", 0) >= NORMAL_THRESHOLDS["safety"]
    )
    return {
        "can_complete": score_ok and not blocking_keys,
        "blocking_keys": list(dict.fromkeys(blocking_keys)),
        "execution": execution,
        "thresholds": dict(NORMAL_THRESHOLDS),
    }
