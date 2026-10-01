from __future__ import annotations

from typing import Any

from intake_execution import evaluate_threshold
from obesity_intake_schema import get_applicable_fields, get_field_definition


FALLBACK_SAFETY_KEYS = ("red_flags", "allergies", "medications", "important_history")


def _attempt_count(key: str, state: dict[str, Any], history: list[dict[str, Any]]) -> int:
    recorded = sum(1 for item in history if item.get("question_key") == key)
    return max(recorded, int(state.get("attempts") or 0))


def select_next_field(
    field_states: dict[str, dict[str, Any]],
    follow_up_answers: list[dict[str, Any]],
    context: dict[str, object] | None = None,
    *,
    ai_available: bool = True,
) -> str | None:
    candidates = []
    for definition in get_applicable_fields(context or {}):
        state = field_states.get(definition.key, {"status": "not_asked"})
        status = state.get("status", "not_asked")
        if status in {"confirmed", "unavailable", "not_applicable"}:
            continue
        if _attempt_count(definition.key, state, follow_up_answers) >= definition.max_attempts:
            continue
        if not ai_available and definition.key not in FALLBACK_SAFETY_KEYS:
            continue

        if definition.key == "red_flags":
            category = 0
        elif definition.hard_required:
            category = 1
        elif state.get("conflicts"):
            category = 2
        elif definition.section == "safety":
            category = 3
        else:
            category = 4
        candidates.append((category, definition.priority, -definition.weight, definition.key))

    if not candidates:
        return None
    candidates.sort()
    return candidates[0][3]


def decide_stop(
    field_states: dict[str, dict[str, Any]],
    execution: dict[str, Any],
    follow_up_answers: list[dict[str, Any]],
    context: dict[str, object] | None = None,
    *,
    red_flags: list[str] | None = None,
    ai_available: bool = True,
) -> dict[str, Any]:
    threshold = evaluate_threshold(execution, field_states, context or {})
    if threshold["can_complete"]:
        return _stop("threshold_reached", complete=True)

    next_key = select_next_field(
        field_states,
        follow_up_answers,
        context or {},
        ai_available=ai_available,
    )
    if next_key:
        return {
            "stop": False,
            "complete": False,
            "reason": "continue_collecting",
            "next_field_key": next_key,
            "blocking_keys": threshold["blocking_keys"],
        }

    if not ai_available:
        return _stop("ai_unavailable", complete=False)

    applicable = get_applicable_fields(context or {})
    unfinished = [
        item for item in applicable
        if field_states.get(item.key, {}).get("status") not in {"confirmed", "not_applicable"}
    ]
    if unfinished and all(field_states.get(item.key, {}).get("status") == "unavailable" for item in unfinished):
        if any(item.hard_required or item.priority <= 5 for item in unfinished):
            return _stop("patient_unavailable", complete=False)
        return _stop("no_collectable_gap", complete=False)

    if any(
        _attempt_count(item.key, field_states.get(item.key, {}), follow_up_answers) >= item.max_attempts
        for item in unfinished
    ):
        return _stop("duplicate_gap", complete=False)
    return _stop("no_collectable_gap", complete=False)


def question_for_field(key: str, attempt_number: int = 1) -> str:
    definition = get_field_definition(key)
    return definition.retry_question if attempt_number >= 2 else definition.question


def _stop(reason: str, *, complete: bool) -> dict[str, Any]:
    return {
        "stop": True,
        "complete": complete,
        "reason": reason,
        "next_field_key": None,
        "blocking_keys": [],
    }
