from __future__ import annotations

from typing import Any

from intake_views import build_doctor_summary
from repository import SqlAlchemyIntakeRepository


def build_doctor_patient_list(repository: SqlAlchemyIntakeRepository) -> list[dict[str, Any]]:
    items = []
    for patient in repository.list_patients():
        patient_id = str(patient["patient_id"])
        sessions = repository.list_patient_sessions(patient_id)
        reports = repository.list_patient_reports(patient_id)
        latest = sessions[0] if sessions else None
        has_safety_alert = any(
            bool((report.get("doctor_summary") or {}).get("safety_alerts"))
            for report in reports
        )
        items.append(
            {
                **patient,
                "record_count": len(reports),
                "unfinished_count": len(repository.list_unfinished_sessions(patient_id)),
                "latest_intake_at": latest["updated_at"] if latest else None,
                "latest_phase": latest["phase"] if latest else None,
                "has_safety_alert": has_safety_alert,
            }
        )
    return items


def build_doctor_patient_detail(
    repository: SqlAlchemyIntakeRepository, patient_id: str
) -> dict[str, Any] | None:
    patient = repository.get_patient(patient_id)
    if patient is None:
        return None
    sessions = repository.list_patient_sessions(patient_id)
    return {
        **patient,
        "sessions": sessions,
        "records": repository.list_patient_reports(patient_id),
    }


def build_doctor_session_summary(
    repository: SqlAlchemyIntakeRepository, session_id: str
) -> dict[str, Any] | None:
    patient_id = repository.get_session_owner(session_id)
    if patient_id is None:
        return None
    state = repository.get_existing_session(patient_id, session_id)
    return build_doctor_summary(state) if state is not None else None
