from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Callable
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from intake_execution import blank_field_states, calculate_execution
from models import (
    AuditEvent,
    BaselineMeasurement,
    FollowUpAnswer,
    IntakeFieldState,
    IntakeReport,
    IntakeSessionModel,
    Patient,
    RecommendedExam,
)
from obesity_intake_schema import RULE_VERSION


OPEN_QUESTION = "这次您最想改善的体重或身体方面的困扰是什么？可以说说什么时候开始，以及最近有什么变化。"


class ConcurrentSessionUpdate(RuntimeError):
    pass


class ArchivedSession(RuntimeError):
    pass


class DeletedReport(RuntimeError):
    pass


# A completed session without a saved report still needs patient review.
TERMINAL_PHASES = ("escalated",)


def _unfinished_stage_label(state: dict[str, Any]) -> str:
    phase = str(state.get("phase") or "baseline_collection")
    if phase == "baseline_collection":
        return "基础资料"
    if phase == "open_intake":
        return "开放描述"
    if phase == "processing":
        return "正在整理"
    if phase == "follow_up":
        return f"第 {len(state.get('follow_up_answers') or []) + 1} 轮补充"
    if phase == "completed":
        return "待核对保存"
    if phase == "incomplete":
        return "资料待补充"
    return "继续问诊"


def _has_meaningful_input(state: dict[str, Any]) -> bool:
    return bool(
        state.get("baseline_confirmed")
        or str(state.get("open_answer") or "").strip()
        or state.get("follow_up_answers")
    )


def create_initial_state(session_id: str, patient_id: str) -> dict[str, Any]:
    context: dict[str, object] = {
        "baseline_confirmed": False,
        "pregnancy_applicable": True,
    }
    field_states = blank_field_states(context)
    return {
        "session_id": session_id,
        "patient_id": patient_id,
        "phase": "baseline_collection",
        "context": context,
        "open_question": OPEN_QUESTION,
        "baseline": None,
        "bmi_assessment": None,
        "baseline_confirmed": False,
        "open_answer": "",
        "latest_answer": "",
        "current_question": "",
        "current_field_key": "",
        "attempt_number": 0,
        "turn": 0,
        "follow_up_answers": [],
        "field_states": field_states,
        "execution": calculate_execution(field_states, context),
        "blocking_keys": [],
        "conflicts": [],
        "safety_alerts": [],
        "recommended_exams": [],
        "stop_reason": None,
        "report_markdown": None,
        "audit": [{"event": "session_created", "turn": 0, "rule_version": RULE_VERSION}],
        "version": 1,
    }


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            pass
    return datetime.now(UTC).replace(tzinfo=None)


class SqlAlchemyIntakeRepository:
    def __init__(self, session_factory: Callable[[], Session]):
        self._session_factory = session_factory

    @staticmethod
    def _patient_payload(row: Patient) -> dict[str, Any]:
        return {
            "patient_id": row.id,
            "display_name": row.display_name or row.id,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    def ensure_patient(self, patient_id: str, display_name: str | None = None) -> dict[str, Any]:
        with self._session_factory.begin() as database:
            row = database.get(Patient, patient_id)
            if row is None:
                row = Patient(id=patient_id, display_name=display_name)
                database.add(row)
                database.flush()
            elif display_name and row.display_name != display_name:
                row.display_name = display_name
                database.flush()
            return self._patient_payload(row)

    def list_patients(self) -> list[dict[str, Any]]:
        with self._session_factory() as database:
            rows = database.scalars(
                select(Patient).order_by(Patient.created_at.asc(), Patient.id.asc())
            ).all()
            return [self._patient_payload(row) for row in rows]

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        with self._session_factory() as database:
            row = database.get(Patient, patient_id)
            return self._patient_payload(row) if row is not None else None

    def list_patient_sessions(self, patient_id: str) -> list[dict[str, Any]]:
        with self._session_factory() as database:
            rows = database.scalars(
                select(IntakeSessionModel)
                .where(
                    IntakeSessionModel.patient_id == patient_id,
                    IntakeSessionModel.archived_at.is_(None),
                )
                .order_by(IntakeSessionModel.updated_at.desc())
            ).all()
            rows = [
                row for row in rows
                if str(row.open_answer or "").strip()
                or bool((row.state_json or {}).get("follow_up_answers"))
                or (row.report is not None and row.report.deleted_at is None)
            ]
            return [
                {
                    "session_id": row.id,
                    "patient_id": row.patient_id,
                    "phase": row.phase,
                    "turn": row.turn,
                    "current_field_key": row.current_field_key or "",
                    "current_question": row.current_question or "",
                    "archived_at": row.archived_at.isoformat() if row.archived_at else None,
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                }
                for row in rows
            ]

    def get_session_owner(self, session_id: str) -> str | None:
        with self._session_factory() as database:
            row = database.get(IntakeSessionModel, session_id)
            return row.patient_id if row is not None else None

    def get_existing_session(self, patient_id: str, session_id: str) -> dict[str, Any] | None:
        with self._session_factory() as database:
            row = database.get(IntakeSessionModel, session_id)
            if row is None or row.patient_id != patient_id:
                return None
            state = deepcopy(row.state_json or {})
            state.update(
                session_id=row.id,
                patient_id=row.patient_id,
                phase=row.phase,
                turn=row.turn,
                current_field_key=row.current_field_key or "",
                current_question=row.current_question or "",
                open_answer=row.open_answer or "",
                report_markdown=row.report_markdown or None,
                version=row.version,
            )
            return state

    def get_or_create_session(
        self, session_id: str, patient_id: str = "demo-zhang"
    ) -> dict[str, Any]:
        with self._session_factory.begin() as database:
            row = database.get(IntakeSessionModel, session_id)
            if row is None:
                patient = database.get(Patient, patient_id)
                if patient is None:
                    database.add(Patient(id=patient_id))
                    database.flush()
                state = create_initial_state(session_id, patient_id)
                row = IntakeSessionModel(
                    id=session_id,
                    patient_id=patient_id,
                    phase=state["phase"],
                    state_json=deepcopy(state),
                    rule_version=RULE_VERSION,
                    version=1,
                )
                database.add(row)
                self._replace_normalized_rows(database, row, state)
                database.flush()
                return deepcopy(state)
            if row.patient_id != patient_id:
                raise KeyError("session does not belong to patient")
            if row.archived_at is not None:
                raise ArchivedSession("session has been archived")
            state = deepcopy(row.state_json or {})
            state.update(
                session_id=row.id,
                patient_id=row.patient_id,
                phase=row.phase,
                turn=row.turn,
                current_field_key=row.current_field_key or "",
                current_question=row.current_question or "",
                open_answer=row.open_answer or "",
                report_markdown=row.report_markdown or None,
                version=row.version,
            )
            return state

    def save_session_state(
        self, state: dict[str, Any], expected_version: int | None = None
    ) -> dict[str, Any]:
        session_id = str(state["session_id"])
        patient_id = str(state.get("patient_id") or "demo-zhang")
        with self._session_factory.begin() as database:
            row = database.get(IntakeSessionModel, session_id)
            if row is None:
                patient = database.get(Patient, patient_id)
                if patient is None:
                    database.add(Patient(id=patient_id))
                    database.flush()
                row = IntakeSessionModel(id=session_id, patient_id=patient_id, version=1)
                database.add(row)
                database.flush()
            if row.patient_id != patient_id:
                raise KeyError("session does not belong to patient")
            if row.archived_at is not None:
                raise ArchivedSession("session has been archived")
            if expected_version is not None and row.version != expected_version:
                raise ConcurrentSessionUpdate(
                    f"session {session_id} changed from version {expected_version} to {row.version}"
                )
            new_version = row.version + 1
            snapshot = deepcopy(state)
            snapshot["patient_id"] = patient_id
            snapshot["version"] = new_version
            row.phase = str(snapshot.get("phase") or "baseline_collection")
            row.turn = int(snapshot.get("turn") or 0)
            row.current_field_key = str(snapshot.get("current_field_key") or "") or None
            row.current_question = str(snapshot.get("current_question") or "") or None
            row.open_answer = str(snapshot.get("open_answer") or "")
            row.report_markdown = str(snapshot.get("report_markdown") or "")
            row.completion_status = snapshot.get("stop_reason")
            row.rule_version = RULE_VERSION
            row.version = new_version
            row.state_json = snapshot
            self._replace_normalized_rows(database, row, snapshot)
            database.flush()
            return deepcopy(snapshot)

    def list_unfinished_sessions(self, patient_id: str) -> list[dict[str, Any]]:
        with self._session_factory() as database:
            rows = database.scalars(
                select(IntakeSessionModel)
                .where(
                    IntakeSessionModel.patient_id == patient_id,
                    IntakeSessionModel.archived_at.is_(None),
                    IntakeSessionModel.phase.not_in(TERMINAL_PHASES),
                )
                .order_by(IntakeSessionModel.updated_at.desc())
            ).all()
            items: list[dict[str, Any]] = []
            for row in rows:
                if row.report is not None:
                    continue
                state = deepcopy(row.state_json or {})
                if not _has_meaningful_input(state):
                    continue
                concern = str(row.open_answer or state.get("open_answer") or "").strip()
                items.append(
                    {
                        "session_id": row.id,
                        "primary_concern": concern[:80] or "尚未填写主要困扰",
                        "phase": row.phase,
                        "stage_label": _unfinished_stage_label(state),
                        "updated_at": row.updated_at.isoformat(),
                    }
                )
            return items

    def archive_session(self, patient_id: str, session_id: str) -> dict[str, Any]:
        with self._session_factory.begin() as database:
            row = database.get(IntakeSessionModel, session_id)
            if row is None or row.patient_id != patient_id:
                raise KeyError("session does not belong to patient")
            if row.archived_at is not None:
                return {"session_id": row.id, "archived_at": row.archived_at.isoformat()}

            archived_at = datetime.now(UTC).replace(tzinfo=None)
            snapshot = deepcopy(row.state_json or {})
            audit = list(snapshot.get("audit") or [])
            audit.append(
                {
                    "event": "session_archived",
                    "turn": int(snapshot.get("turn") or row.turn or 0),
                    "archived_at": archived_at.isoformat(),
                    "rule_version": RULE_VERSION,
                }
            )
            snapshot["audit"] = audit
            snapshot["version"] = row.version + 1
            row.archived_at = archived_at
            row.updated_at = archived_at
            row.version += 1
            row.state_json = snapshot
            self._replace_normalized_rows(database, row, snapshot)
            database.flush()
            return {"session_id": row.id, "archived_at": archived_at.isoformat()}

    def _replace_normalized_rows(
        self, database: Session, row: IntakeSessionModel, state: dict[str, Any]
    ) -> None:
        session_id = row.id
        baseline = state.get("baseline")
        existing_baseline = database.scalar(
            select(BaselineMeasurement).where(BaselineMeasurement.session_id == session_id)
        )
        if baseline:
            payload = {**baseline, "bmi_assessment": state.get("bmi_assessment")}
            if existing_baseline is None:
                database.add(
                    BaselineMeasurement(
                        session_id=session_id,
                        payload_json=payload,
                        bmi=(state.get("bmi_assessment") or {}).get("bmi"),
                        confirmed=bool(state.get("baseline_confirmed")),
                    )
                )
            else:
                existing_baseline.payload_json = payload
                existing_baseline.bmi = (state.get("bmi_assessment") or {}).get("bmi")
                existing_baseline.confirmed = bool(state.get("baseline_confirmed"))
        elif existing_baseline is not None:
            database.delete(existing_baseline)

        database.execute(delete(IntakeFieldState).where(IntakeFieldState.session_id == session_id))
        database.add_all(
            IntakeFieldState(session_id=session_id, field_key=key, state_json=deepcopy(value))
            for key, value in (state.get("field_states") or {}).items()
        )
        database.execute(delete(FollowUpAnswer).where(FollowUpAnswer.session_id == session_id))
        for sequence_no, answer in enumerate(state.get("follow_up_answers") or [], start=1):
            database.add(
                FollowUpAnswer(
                    session_id=session_id,
                    sequence_no=sequence_no,
                    question=str(answer.get("question") or ""),
                    answer=str(answer.get("answer") or ""),
                    question_key=answer.get("question_key"),
                    question_kind=answer.get("question_kind"),
                    attempt_number=answer.get("attempt_number"),
                    answer_quality=answer.get("answer_quality"),
                    payload_json=deepcopy(answer),
                    created_at=_parse_datetime(answer.get("created_at")),
                )
            )
        database.execute(delete(RecommendedExam).where(RecommendedExam.session_id == session_id))
        database.add_all(
            RecommendedExam(session_id=session_id, sequence_no=index, payload_json=deepcopy(exam))
            for index, exam in enumerate(state.get("recommended_exams") or [], start=1)
        )
        database.execute(delete(AuditEvent).where(AuditEvent.session_id == session_id))
        for sequence_no, event in enumerate(state.get("audit") or [], start=1):
            database.add(
                AuditEvent(
                    session_id=session_id,
                    sequence_no=sequence_no,
                    event_type=str(event.get("event") or "state_event"),
                    turn=event.get("turn"),
                    field_key=event.get("field_key"),
                    payload_json=deepcopy(event),
                    rule_version=event.get("rule_version"),
                )
            )

    def save_report(self, patient_id: str, record: dict[str, Any]) -> dict[str, Any]:
        session_id = str(record["session_id"])
        with self._session_factory.begin() as database:
            session_row = database.get(IntakeSessionModel, session_id)
            if session_row is None:
                patient = database.get(Patient, patient_id)
                if patient is None:
                    database.add(Patient(id=patient_id))
                    database.flush()
                session_row = IntakeSessionModel(
                    id=session_id,
                    patient_id=patient_id,
                    state_json=create_initial_state(session_id, patient_id),
                )
                database.add(session_row)
                database.flush()
            if session_row.patient_id != patient_id:
                raise KeyError("session does not belong to patient")
            report = database.scalar(
                select(IntakeReport).where(IntakeReport.session_id == session_id)
            )
            payload = deepcopy(record)
            if report is None:
                record_id = str(record.get("record_id") or uuid4())
                payload["record_id"] = record_id
                payload["patient_id"] = patient_id
                report = IntakeReport(id=record_id, session_id=session_id, patient_id=patient_id)
                database.add(report)
            else:
                payload["record_id"] = report.id
                payload["patient_id"] = patient_id
            report.completion_status = record.get("stop_reason")
            report.report_markdown = str(
                record.get("markdown_table") or record.get("report_markdown") or ""
            )
            report.rule_version = record.get("rule_version")
            report.payload_json = payload
            if record.get("created_at") and report.created_at is None:
                report.created_at = _parse_datetime(record["created_at"])
            database.flush()
            return deepcopy(payload)

    def list_patient_reports(self, patient_id: str) -> list[dict[str, Any]]:
        with self._session_factory() as database:
            rows = database.scalars(
                select(IntakeReport)
                .where(
                    IntakeReport.patient_id == patient_id,
                    IntakeReport.deleted_at.is_(None),
                )
                .order_by(IntakeReport.created_at.desc())
            ).all()
            return [deepcopy(row.payload_json) for row in rows]

    def get_patient_report(self, patient_id: str, record_id: str) -> dict[str, Any] | None:
        with self._session_factory() as database:
            row = database.scalar(
                select(IntakeReport).where(
                    IntakeReport.id == record_id,
                    IntakeReport.patient_id == patient_id,
                )
            )
            if row is not None and row.deleted_at is not None:
                raise DeletedReport("report has been deleted")
            return deepcopy(row.payload_json) if row is not None else None

    def soft_delete_report(self, patient_id: str, record_id: str) -> dict[str, str]:
        with self._session_factory.begin() as database:
            row = database.get(IntakeReport, record_id)
            if row is None or row.patient_id != patient_id:
                raise KeyError("report does not belong to patient")
            if row.deleted_at is None:
                row.deleted_at = datetime.now(UTC).replace(tzinfo=None)
                database.flush()
            return {"record_id": row.id, "deleted_at": row.deleted_at.isoformat()}

    def get_report_for_session(self, patient_id: str, session_id: str) -> dict[str, Any] | None:
        with self._session_factory() as database:
            row = database.scalar(
                select(IntakeReport).where(
                    IntakeReport.session_id == session_id,
                    IntakeReport.patient_id == patient_id,
                )
            )
            return deepcopy(row.payload_json) if row is not None else None

    def count_reports(self) -> int:
        with self._session_factory() as database:
            return len(database.scalars(select(IntakeReport.id)).all())

    def list_report_ownership_candidates(self) -> list[dict[str, Any]]:
        """Return every report, including soft-deleted rows, for one-time migration."""
        with self._session_factory() as database:
            rows = database.scalars(
                select(IntakeReport).order_by(IntakeReport.created_at.asc())
            ).all()
            return [
                {
                    "record_id": row.id,
                    "session_id": row.session_id,
                    "patient_id": row.patient_id,
                    "patient_name": (row.payload_json or {}).get("patient_name"),
                }
                for row in rows
            ]

    def reassign_report_ownership(
        self, record_id: str, target_patient_id: str
    ) -> tuple[bool, bool]:
        """Move a report and its session together while preserving child records."""
        with self._session_factory.begin() as database:
            report = database.get(IntakeReport, record_id)
            if report is None:
                raise KeyError("report does not exist")
            session_row = database.get(IntakeSessionModel, report.session_id)
            if session_row is None:
                raise KeyError("report session does not exist")
            if database.get(Patient, target_patient_id) is None:
                database.add(Patient(id=target_patient_id))
                database.flush()

            report_changed = report.patient_id != target_patient_id
            session_changed = session_row.patient_id != target_patient_id
            if report_changed:
                report.patient_id = target_patient_id
                report_payload = deepcopy(report.payload_json or {})
                report_payload["patient_id"] = target_patient_id
                report.payload_json = report_payload
            if session_changed:
                session_row.patient_id = target_patient_id
                session_payload = deepcopy(session_row.state_json or {})
                session_payload["patient_id"] = target_patient_id
                session_row.state_json = session_payload
            database.flush()
            return report_changed, session_changed

    def reassign_legacy_patient_sessions(
        self, source_patient_id: str, target_patient_id: str, dry_run: bool = False
    ) -> int:
        """Move legacy sessions not covered by report migration and retire the old patient."""
        with self._session_factory.begin() as database:
            rows = database.scalars(
                select(IntakeSessionModel).where(
                    IntakeSessionModel.patient_id == source_patient_id,
                    ~IntakeSessionModel.report.has(),
                )
            ).all()
            if dry_run:
                return len(rows)
            if database.get(Patient, target_patient_id) is None:
                database.add(Patient(id=target_patient_id))
                database.flush()
            for row in rows:
                row.patient_id = target_patient_id
                snapshot = deepcopy(row.state_json or {})
                snapshot["patient_id"] = target_patient_id
                row.state_json = snapshot
            database.flush()
            source = database.get(Patient, source_patient_id)
            remaining_reports = database.scalar(
                select(IntakeReport.id).where(IntakeReport.patient_id == source_patient_id).limit(1)
            )
            if source is not None and remaining_reports is None:
                database.delete(source)
            return len(rows)

    def clear(self) -> None:
        with self._session_factory.begin() as database:
            database.execute(delete(Patient))
