from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    sessions: Mapped[list[IntakeSessionModel]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class IntakeSessionModel(Base):
    __tablename__ = "intake_sessions"
    __table_args__ = (UniqueConstraint("patient_id", "id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    phase: Mapped[str] = mapped_column(String(40), default="baseline_collection")
    turn: Mapped[int] = mapped_column(Integer, default=0)
    current_field_key: Mapped[str | None] = mapped_column(String(100))
    current_question: Mapped[str | None] = mapped_column(Text)
    open_answer: Mapped[str] = mapped_column(Text, default="")
    report_markdown: Mapped[str] = mapped_column(Text, default="")
    completion_status: Mapped[str | None] = mapped_column(String(50))
    rule_version: Mapped[str | None] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    state_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    patient: Mapped[Patient] = relationship(back_populates="sessions")
    baseline: Mapped[BaselineMeasurement | None] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )
    field_states: Mapped[list[IntakeFieldState]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    answers: Mapped[list[FollowUpAnswer]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    exams: Mapped[list[RecommendedExam]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list[AuditEvent]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    report: Mapped[IntakeReport | None] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )


class BaselineMeasurement(Base):
    __tablename__ = "baseline_measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("intake_sessions.id", ondelete="CASCADE"), unique=True, index=True
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    bmi: Mapped[float | None] = mapped_column(Float)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    session: Mapped[IntakeSessionModel] = relationship(back_populates="baseline")


class IntakeFieldState(Base):
    __tablename__ = "intake_field_states"
    __table_args__ = (UniqueConstraint("session_id", "field_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("intake_sessions.id", ondelete="CASCADE"), index=True
    )
    field_key: Mapped[str] = mapped_column(String(100))
    state_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    session: Mapped[IntakeSessionModel] = relationship(back_populates="field_states")


class FollowUpAnswer(Base):
    __tablename__ = "follow_up_answers"
    __table_args__ = (UniqueConstraint("session_id", "sequence_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("intake_sessions.id", ondelete="CASCADE"), index=True
    )
    sequence_no: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text, default="")
    answer: Mapped[str] = mapped_column(Text, default="")
    question_key: Mapped[str | None] = mapped_column(String(100))
    question_kind: Mapped[str | None] = mapped_column(String(50))
    attempt_number: Mapped[int | None] = mapped_column(Integer)
    answer_quality: Mapped[str | None] = mapped_column(String(50))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    session: Mapped[IntakeSessionModel] = relationship(back_populates="answers")


class RecommendedExam(Base):
    __tablename__ = "recommended_exams"
    __table_args__ = (UniqueConstraint("session_id", "sequence_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("intake_sessions.id", ondelete="CASCADE"), index=True
    )
    sequence_no: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    session: Mapped[IntakeSessionModel] = relationship(back_populates="exams")


class IntakeReport(Base):
    __tablename__ = "intake_reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("intake_sessions.id", ondelete="CASCADE"), unique=True, index=True
    )
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    completion_status: Mapped[str | None] = mapped_column(String(50))
    report_markdown: Mapped[str] = mapped_column(Text, default="")
    rule_version: Mapped[str | None] = mapped_column(String(80))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    session: Mapped[IntakeSessionModel] = relationship(back_populates="report")
    reviews: Mapped[list[DoctorReview]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (UniqueConstraint("session_id", "sequence_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("intake_sessions.id", ondelete="CASCADE"), index=True
    )
    sequence_no: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(80))
    turn: Mapped[int | None] = mapped_column(Integer)
    field_key: Mapped[str | None] = mapped_column(String(100))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    rule_version: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    session: Mapped[IntakeSessionModel] = relationship(back_populates="audit_events")


class DoctorReview(Base):
    __tablename__ = "doctor_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(
        ForeignKey("intake_reports.id", ondelete="CASCADE"), index=True
    )
    doctor_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(40), default="pending")
    review_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    report: Mapped[IntakeReport] = relationship(back_populates="reviews")


Index("ix_intake_sessions_patient_created", IntakeSessionModel.patient_id, IntakeSessionModel.created_at)
Index(
    "ix_intake_sessions_patient_archived_updated",
    IntakeSessionModel.patient_id,
    IntakeSessionModel.archived_at,
    IntakeSessionModel.updated_at,
)
Index("ix_intake_reports_patient_created", IntakeReport.patient_id, IntakeReport.created_at)
Index(
    "ix_intake_reports_patient_deleted_created",
    IntakeReport.patient_id,
    IntakeReport.deleted_at,
    IntakeReport.created_at,
)
