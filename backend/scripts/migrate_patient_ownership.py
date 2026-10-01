from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass

import db
from patient_directory import seed_demo_patients
from repository import SqlAlchemyIntakeRepository


@dataclass(frozen=True)
class MigrationSummary:
    scanned_reports: int = 0
    updated_reports: int = 0
    updated_sessions: int = 0
    dry_run: bool = False


def patient_id_for_name(name: str | None) -> str:
    normalized = (name or "").strip()
    if "张" in normalized:
        return "patient-zhang"
    if "马" in normalized:
        return "patient-ma"
    if "李" in normalized:
        return "patient-li"
    return "unassigned"


def migrate_patient_ownership(
    repository: SqlAlchemyIntakeRepository, dry_run: bool = False
) -> MigrationSummary:
    seed_demo_patients(repository)
    candidates = repository.list_report_ownership_candidates()
    updated_reports = 0
    updated_sessions = 0
    for item in candidates:
        target_patient_id = patient_id_for_name(item.get("patient_name"))
        if item["patient_id"] == target_patient_id:
            continue
        if dry_run:
            updated_reports += 1
            sessions = repository.list_patient_sessions(str(item["patient_id"]))
            if any(row["session_id"] == item["session_id"] for row in sessions):
                updated_sessions += 1
            continue
        report_changed, session_changed = repository.reassign_report_ownership(
            str(item["record_id"]), target_patient_id
        )
        updated_reports += int(report_changed)
        updated_sessions += int(session_changed)
    updated_sessions += repository.reassign_legacy_patient_sessions(
        "demo-zhang", "patient-zhang", dry_run=dry_run
    )
    return MigrationSummary(
        scanned_reports=len(candidates),
        updated_reports=updated_reports,
        updated_sessions=updated_sessions,
        dry_run=dry_run,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate intake ownership to demo patients")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if db.SessionLocal is None:
        raise SystemExit("DATABASE_URL is required")
    summary = migrate_patient_ownership(
        SqlAlchemyIntakeRepository(db.SessionLocal), dry_run=args.dry_run
    )
    print(asdict(summary))


if __name__ == "__main__":
    main()
