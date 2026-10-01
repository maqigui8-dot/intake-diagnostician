from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


KNOWN_KEYS = {
    "record_id",
    "patient_id",
    "session_id",
    "patient_name",
    "created_at",
    "collected_info",
    "structured_answers",
    "follow_up_answers",
    "markdown_table",
    "recommended_exams",
    "bmi_assessment",
    "skill_analysis",
    "stop_reason",
    "rule_version",
    "doctor_summary",
}


@dataclass
class MigrationSummary:
    scanned: int = 0
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


def _load_record(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("record root must be an object")
    record_id = str(payload.get("record_id") or path.stem)
    payload["record_id"] = record_id
    payload["patient_id"] = str(payload.get("patient_id") or "demo-zhang")
    payload["session_id"] = str(payload.get("session_id") or f"legacy-{record_id}")
    payload.setdefault("follow_up_answers", [])
    payload.setdefault("recommended_exams", [])
    payload.setdefault("markdown_table", "")
    return payload


def import_record(path: Path, repository, dry_run: bool = False) -> str:
    record = _load_record(path)
    patient_id = record["patient_id"]
    if repository.get_patient_report(patient_id, record["record_id"]) is not None:
        return "skipped"
    if repository.get_report_for_session(patient_id, record["session_id"]) is not None:
        return "skipped"
    if dry_run:
        return "imported"

    state = repository.get_or_create_session(record["session_id"], patient_id)
    state.update(
        {
            "follow_up_answers": list(record.get("follow_up_answers") or []),
            "recommended_exams": list(record.get("recommended_exams") or []),
            "bmi_assessment": record.get("bmi_assessment"),
            "report_markdown": record.get("markdown_table") or "",
            "phase": "completed",
            "stop_reason": record.get("stop_reason") or "legacy_import",
        }
    )
    extra = {key: value for key, value in record.items() if key not in KNOWN_KEYS}
    state["audit"].append(
        {
            "event": "legacy_record_imported",
            "turn": state.get("turn", 0),
            "source_file": path.name,
            "unmapped": extra,
        }
    )
    repository.save_session_state(state, expected_version=state.get("version"))
    repository.save_report(patient_id, record)
    return "imported"


def migrate_directory(path: Path, repository, dry_run: bool = False) -> MigrationSummary:
    summary = MigrationSummary()
    for source in sorted(Path(path).glob("*.json")):
        summary.scanned += 1
        try:
            result = import_record(source, repository, dry_run=dry_run)
            if result == "skipped":
                summary.skipped += 1
            else:
                summary.imported += 1
        except Exception as exc:
            summary.failed += 1
            summary.errors.append(f"{source.name}: {exc}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Import legacy JSON records into MySQL")
    parser.add_argument("--records-dir", type=Path, default=Path(__file__).parents[1] / "records")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    from db import SessionLocal
    from repository import SqlAlchemyIntakeRepository

    if SessionLocal is None:
        print("DATABASE_URL is required", file=sys.stderr)
        return 2
    summary = migrate_directory(
        args.records_dir,
        SqlAlchemyIntakeRepository(SessionLocal),
        dry_run=args.dry_run,
    )
    print(json.dumps(summary.__dict__, ensure_ascii=False, indent=2))
    return 1 if summary.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
