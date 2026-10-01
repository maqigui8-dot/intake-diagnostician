from __future__ import annotations

from collections.abc import Mapping

from repository import SqlAlchemyIntakeRepository


DEMO_PATIENTS: dict[str, str] = {
    "patient-zhang": "张女士",
    "patient-ma": "马先生",
    "patient-li": "李女士",
    "unassigned": "待归属患者",
}


def seed_demo_patients(
    repository: SqlAlchemyIntakeRepository,
    patients: Mapping[str, str] = DEMO_PATIENTS,
) -> list[dict[str, object]]:
    """Create or refresh the fixed demo patient directory without duplicates."""
    return [
        repository.ensure_patient(patient_id, display_name)
        for patient_id, display_name in patients.items()
    ]
