from __future__ import annotations

from typing import Any

from intake_execution import evaluate_patient_readiness
from obesity_intake_schema import get_applicable_fields, get_field_definition


CLARIFICATION_PATTERNS = (
    "这是什么",
    "什么意思",
    "没听懂",
    "没明白",
    "能解释",
    "请解释",
)


def is_clarification_request(answer: str) -> bool:
    compact = "".join(str(answer or "").split()).rstrip("？?!！。")
    return len(compact) <= 24 and any(item in compact for item in CLARIFICATION_PATTERNS)


def _attempt_count(key: str, state: dict[str, Any], history: list[dict[str, Any]]) -> int:
    recorded = sum(
        1
        for item in history
        if item.get("question_key") == key and item.get("answer_quality") != "clarification"
    )
    return max(recorded, int(state.get("attempts") or 0))


def _has_unresolved_conflict(state: dict[str, Any]) -> bool:
    return any(
        isinstance(conflict, dict) and not conflict.get("resolved", False)
        for conflict in state.get("conflicts") or []
    )


def select_next_field(
    field_states: dict[str, dict[str, Any]],
    follow_up_answers: list[dict[str, Any]],
    context: dict[str, object] | None = None,
    *,
    ai_available: bool = True,
    field_keys: set[str] | None = None,
) -> str | None:
    candidates = []
    for definition in get_applicable_fields(context or {}):
        if field_keys is not None and definition.key not in field_keys:
            continue
        state = field_states.get(definition.key, {"status": "not_asked"})
        status = state.get("status", "not_asked")
        has_conflict = _has_unresolved_conflict(state)
        if definition.layer == "baseline":
            continue
        if status in {"unavailable", "not_applicable"}:
            continue
        if status == "confirmed" and not has_conflict:
            continue
        if _attempt_count(definition.key, state, follow_up_answers) >= definition.max_attempts:
            continue

        layer_order = {"safety": 0, "risk": 1, "tcm": 2}
        candidates.append((
            layer_order.get(definition.layer, 3),
            0 if has_conflict else 1,
            definition.priority,
            -definition.weight,
            definition.key,
        ))

    if not candidates:
        return None
    candidates.sort()
    return candidates[0][4]


def decide_stop(
    field_states: dict[str, dict[str, Any]],
    execution: dict[str, Any],
    follow_up_answers: list[dict[str, Any]],
    context: dict[str, object] | None = None,
    *,
    red_flags: list[str] | None = None,
    ai_available: bool = True,
) -> dict[str, Any]:
    readiness = evaluate_patient_readiness(field_states, context or {})
    if readiness["can_complete"]:
        return _stop("core_information_ready", complete=True, blocking_keys=[])

    next_key = select_next_field(
        field_states,
        follow_up_answers,
        context or {},
        ai_available=ai_available,
        field_keys=set(readiness["core_field_keys"]),
    )
    if next_key:
        return {
            "stop": False,
            "complete": False,
            "reason": "continue_collecting",
            "next_field_key": next_key,
            "blocking_keys": readiness["blocking_keys"],
        }

    applicable = [
        item for item in get_applicable_fields(context or {})
        if item.key in readiness["core_field_keys"]
    ]
    unfinished = [
        item for item in applicable
        if field_states.get(item.key, {}).get("status") not in {"confirmed", "not_applicable"}
    ]
    if unfinished and all(field_states.get(item.key, {}).get("status") == "unavailable" for item in unfinished):
        if any(item.hard_required or item.priority <= 5 for item in unfinished):
            return _stop("patient_unavailable", complete=False, blocking_keys=readiness["blocking_keys"])
        return _stop("no_collectable_gap", complete=False, blocking_keys=readiness["blocking_keys"])

    if any(
        _attempt_count(item.key, field_states.get(item.key, {}), follow_up_answers) >= item.max_attempts
        for item in unfinished
    ):
        return _stop("duplicate_gap", complete=False, blocking_keys=readiness["blocking_keys"])
    return _stop("no_collectable_gap", complete=False, blocking_keys=readiness["blocking_keys"])


def question_for_field(key: str, attempt_number: int = 1) -> str:
    definition = get_field_definition(key)
    return definition.retry_question if attempt_number >= 2 else definition.question


def _stop(
    reason: str,
    *,
    complete: bool,
    blocking_keys: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "stop": True,
        "complete": complete,
        "reason": reason,
        "next_field_key": None,
        "blocking_keys": list(blocking_keys or []),
    }
