from __future__ import annotations

from copy import deepcopy
import hashlib
import re
from typing import Any


def normalize_follow_up_key(value: Any) -> str:
    key = re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower())
    return re.sub(r"_+", "_", key).strip("_")[:80]


def _fallback_key(analysis: dict[str, Any]) -> str:
    candidates = analysis.get("missing_required_items") or analysis.get("follow_up_questions") or []
    if not candidates:
        return ""
    source = str(candidates[0]).strip()
    if not source:
        return ""
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"gap_{digest}"


def _stop_follow_up(result: dict[str, Any], reason: str, *, mark_complete: bool = False) -> dict[str, Any]:
    result["follow_up_questions"] = []
    result["completion_reason"] = reason
    if mark_complete:
        result["completeness_status"] = "complete"
    return result


def apply_follow_up_policy(analysis: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(analysis)
    if result.get("status") != "completed":
        return result

    questions = result.get("follow_up_questions") or []
    if result.get("completeness_status") == "complete" or not questions:
        result["follow_up_questions"] = []
        result.setdefault("completion_reason", "information_complete")
        return result

    raw_key = result.get("follow_up_key")
    question_key = normalize_follow_up_key(raw_key) or _fallback_key(result)
    question_kind = str(result.get("follow_up_kind") or "required").strip().lower()
    if question_kind not in {"required", "optional"}:
        question_kind = "required"

    result["follow_up_key"] = question_key
    result["follow_up_kind"] = question_kind

    follow_up_answers = state.get("follow_up_answers") or []

    if question_kind != "required":
        return _stop_follow_up(result, "optional_only", mark_complete=True)

    attempted_keys = {
        normalize_follow_up_key(item.get("question_key"))
        for item in follow_up_answers
        if isinstance(item, dict) and item.get("question_key")
    }
    if question_key and question_key in attempted_keys:
        return _stop_follow_up(result, "duplicate_gap")

    result["completion_reason"] = "continue_required_gap"
    return result
