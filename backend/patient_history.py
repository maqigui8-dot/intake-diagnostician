from __future__ import annotations

from typing import Any


DEMO_PATIENT_ID = "demo-zhang"
DEFAULT_CONCERN = "本次诊前问诊"


def belongs_to_patient(record: dict[str, Any], patient_id: str) -> bool:
    """Only records explicitly saved for the active patient are visible."""
    return record.get("patient_id") == patient_id


def find_record_for_session(
    records: list[dict[str, Any]], patient_id: str, session_id: str
) -> dict[str, Any] | None:
    """Find an existing saved record without crossing patient boundaries."""
    if not session_id:
        return None
    return next(
        (
            record
            for record in records
            if belongs_to_patient(record, patient_id)
            and record.get("session_id") == session_id
        ),
        None,
    )


def _primary_concern(record: dict[str, Any]) -> str:
    collected_info = record.get("collected_info") or {}
    return str(collected_info.get("开放描述") or DEFAULT_CONCERN).strip() or DEFAULT_CONCERN


def make_history_item(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record.get("record_id", ""),
        "created_at": record.get("created_at", ""),
        "primary_concern": _primary_concern(record),
        "status": "资料已整理",
    }


def make_patient_history_detail(record: dict[str, Any]) -> dict[str, Any]:
    """Return the saved patient-facing snapshot without doctor-only metadata."""
    item = make_history_item(record)
    return {
        **item,
        "report_markdown": record.get("markdown_table", ""),
        "follow_up_answers": list(record.get("follow_up_answers") or []),
        "recommended_exams": list(record.get("recommended_exams") or []),
        "bmi_assessment": record.get("bmi_assessment"),
    }
