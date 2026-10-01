"""
中医诊前问诊子智能体 - 后端服务
FastAPI + Deep Agents (LangGraph)
"""
import os
import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

load_dotenv()

import db
from db import check_database, check_database_revision
from repository import (
    ArchivedSession,
    ConcurrentSessionUpdate,
    DeletedReport,
    SqlAlchemyIntakeRepository,
)

from agent import (
    create_intake_analysis_agent,
    create_tcm_agent,
    sessions,
)
from intake_flow import (
    complete_intake_session,
    configure_intake_repository,
    correct_patient_field,
    create_intake_session,
    get_internal_intake_state,
    get_intake_state,
    move_intake,
    require_baseline_confirmation,
    set_baseline,
    submit_follow_up_answer,
    submit_intake_answer,
    submit_open_answer,
)
from intake_views import build_doctor_summary, build_patient_state
from intake_execution import evaluate_patient_readiness
from patient_directory import seed_demo_patients
from patient_history import (
    DEMO_PATIENT_ID,
    belongs_to_patient,
    find_record_for_session,
    make_history_item,
    make_patient_history_detail,
)
from skill_analysis import analyze_intake_with_agent, process_intake_turn, unavailable_analysis

@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not check_database() or db.SessionLocal is None:
        raise RuntimeError("Database is unavailable")
    if not check_database_revision():
        raise RuntimeError("Database migration is not at the required revision")
    repository = SqlAlchemyIntakeRepository(db.SessionLocal)
    seed_demo_patients(repository)
    configure_intake_repository(repository)
    configure_report_repository(repository)
    try:
        yield
    finally:
        configure_report_repository(None)
        configure_intake_repository(None)


app = FastAPI(title="AI老中医问诊", version="4.0.0-deepagent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ConcurrentSessionUpdate)
async def handle_concurrent_session_update(_request, _error):
    return JSONResponse(
        status_code=409,
        content={"detail": "问诊资料已在其他请求中更新，请刷新后重试。"},
    )


@app.exception_handler(ArchivedSession)
async def handle_archived_session(_request, _error):
    return JSONResponse(
        status_code=410,
        content={"detail": "该问诊已被放弃，请新建问诊后继续。"},
    )


@app.exception_handler(DeletedReport)
async def handle_deleted_report(_request, _error):
    return JSONResponse(
        status_code=410,
        content={"detail": "该档案已删除。"},
    )

ANALYSIS_TIMEOUT_SECONDS = 45

RECORDS_DIR = Path(__file__).parent / "records"
RECORDS_DIR.mkdir(exist_ok=True)

# 启动时初始化 Agent（全局单例）
_tcm_agent = None
_intake_analysis_agent = None
_report_repository = None


def configure_report_repository(repository=None):
    global _report_repository
    _report_repository = repository


def get_agent():
    global _tcm_agent
    if _tcm_agent is None:
        _tcm_agent = create_tcm_agent()
    return _tcm_agent


def get_analysis_agent():
    global _intake_analysis_agent
    if _intake_analysis_agent is None:
        _intake_analysis_agent = create_intake_analysis_agent()
    return _intake_analysis_agent


# ============================================================
# 请求 / 响应模型（与前端兼容）
# ============================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    table: Optional[str] = None
    is_complete: bool = False
    collected_info: Optional[dict] = None


class SaveRecordRequest(BaseModel):
    session_id: str
    patient_id: str = DEMO_PATIENT_ID
    patient_name: str = ""
    collected_info: dict = Field(default_factory=dict)
    structured_answers: dict = Field(default_factory=dict)
    follow_up_answers: list[dict] = Field(default_factory=list)
    markdown_table: str = ""
    skill_analysis: dict = Field(default_factory=dict)


class IntakeCorrectionRequest(BaseModel):
    field_key: str
    value: str


class PatientSaveRequest(BaseModel):
    patient_confirmed: bool


class IntakeAnswerRequest(BaseModel):
    question_id: str
    option_id: str
    note: str = ""


class IntakeOpenAnswerRequest(BaseModel):
    answer: str


class BaselineRequest(BaseModel):
    age: int | float | str | None = None
    sex: str | None = None
    height_cm: int | float | str | None = None
    weight_kg: int | float | str | None = None
    waist_cm: int | float | str | None = None
    hip_cm: int | float | str | None = None
    measured_at: str | None = None


class IntakeMoveRequest(BaseModel):
    direction: str


class IntakeFollowUpRequest(BaseModel):
    answer: str
    question: str = ""
    question_key: str = ""
    question_kind: str = "required"


class SessionCreateRequest(BaseModel):
    session_id: str | None = None


# ============================================================
# 辅助函数
# ============================================================

def extract_last_ai_message(messages: list) -> str:
    """从消息列表中提取最后一条 AI 消息的内容"""
    for m in reversed(messages):
        t = getattr(m, "type", None)
        content = getattr(m, "content", "")
        if t == "ai" and content:
            return str(content)
    return "（小郎中正在思考……）"


def save_record_to_file(record_id: str, data: dict):
    filepath = RECORDS_DIR / f"{record_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_all_records() -> list[dict]:
    records = []
    for fp in sorted(
        RECORDS_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                records.append(json.load(f))
        except Exception:
            continue
    return records


def load_record(record_id: str) -> Optional[dict]:
    filepath = RECORDS_DIR / f"{record_id}.json"
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# API 路由
# ============================================================

def _require_repository() -> SqlAlchemyIntakeRepository:
    if _report_repository is None:
        raise HTTPException(status_code=503, detail="数据库暂不可用")
    return _report_repository


def _require_patient(patient_id: str) -> SqlAlchemyIntakeRepository:
    repository = _require_repository()
    if repository.get_patient(patient_id) is None:
        raise HTTPException(status_code=404, detail="患者不存在")
    return repository


def _require_owned_session(patient_id: str, session_id: str) -> SqlAlchemyIntakeRepository:
    repository = _require_patient(patient_id)
    if repository.get_existing_session(patient_id, session_id) is None:
        raise HTTPException(status_code=404, detail="问诊不存在")
    return repository


@app.get("/api/patients")
async def list_patients():
    return _require_repository().list_patients()


@app.post("/api/patients/{patient_id}/sessions")
async def create_scoped_intake_session(patient_id: str, req: SessionCreateRequest):
    _require_patient(patient_id)
    session_id = req.session_id or str(uuid.uuid4())
    return build_patient_state(create_intake_session(patient_id, session_id))


@app.get("/api/patients/{patient_id}/sessions/unfinished")
async def list_scoped_unfinished_sessions(patient_id: str):
    return _require_patient(patient_id).list_unfinished_sessions(patient_id)


@app.get("/api/patients/{patient_id}/sessions/{session_id}")
async def get_scoped_intake_session(patient_id: str, session_id: str):
    _require_owned_session(patient_id, session_id)
    return build_patient_state(get_intake_state(session_id, patient_id))


@app.post("/api/patients/{patient_id}/sessions/{session_id}/baseline")
async def submit_scoped_baseline(patient_id: str, session_id: str, req: BaselineRequest):
    _require_owned_session(patient_id, session_id)
    try:
        return build_patient_state(set_baseline(session_id, req.model_dump(), patient_id))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/patients/{patient_id}/sessions/{session_id}/open-answer")
async def answer_scoped_open_intake(patient_id: str, session_id: str, req: IntakeOpenAnswerRequest):
    _require_owned_session(patient_id, session_id)
    try:
        return build_patient_state(submit_open_answer(session_id, req.answer, patient_id))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/patients/{patient_id}/sessions/{session_id}/follow-up")
async def answer_scoped_follow_up(patient_id: str, session_id: str, req: IntakeFollowUpRequest):
    _require_owned_session(patient_id, session_id)
    try:
        return build_patient_state(submit_follow_up_answer(session_id, req.answer))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/patients/{patient_id}/sessions/{session_id}/analyze")
async def analyze_scoped_intake(patient_id: str, session_id: str):
    _require_owned_session(patient_id, session_id)
    return await analyze_structured_intake(session_id)


@app.post("/api/patients/{patient_id}/sessions/{session_id}/corrections")
async def correct_scoped_intake_field(
    patient_id: str, session_id: str, req: IntakeCorrectionRequest,
):
    repository = _require_owned_session(patient_id, session_id)
    if repository.get_report_for_session(patient_id, session_id) is not None:
        raise HTTPException(status_code=409, detail="档案已保存，不能在此修改；如有新的情况请重新问诊。")
    try:
        return build_patient_state(correct_patient_field(session_id, req.field_key, req.value, patient_id))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/patients/{patient_id}/sessions/{session_id}/save")
async def save_scoped_patient_record(
    patient_id: str, session_id: str, req: PatientSaveRequest,
):
    repository = _require_owned_session(patient_id, session_id)
    if not req.patient_confirmed:
        raise HTTPException(status_code=400, detail="请先核对关键资料，再确认保存。")
    patient = repository.get_patient(patient_id) or {}
    return await save_record(SaveRecordRequest(
        session_id=session_id,
        patient_id=patient_id,
        patient_name=patient.get("display_name") or "演示患者",
    ))


@app.post("/api/patients/{patient_id}/sessions/{session_id}/archive")
async def archive_scoped_intake_session(patient_id: str, session_id: str):
    repository = _require_owned_session(patient_id, session_id)
    return repository.archive_session(patient_id, session_id)


@app.get("/api/patients/{patient_id}/records")
async def list_scoped_patient_records(patient_id: str):
    records = _require_patient(patient_id).list_patient_reports(patient_id)
    return [make_history_item(record) for record in records]


@app.get("/api/patients/{patient_id}/records/{record_id}")
async def get_scoped_patient_record(patient_id: str, record_id: str):
    record = _require_patient(patient_id).get_patient_report(patient_id, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return make_patient_history_detail(record)


@app.post("/api/patients/{patient_id}/records/{record_id}/delete")
async def delete_scoped_patient_record(patient_id: str, record_id: str):
    repository = _require_patient(patient_id)
    try:
        return repository.soft_delete_report(patient_id, record_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="记录不存在") from error


async def chat(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 如果已完成，拒绝继续对话
    if sessions.is_complete(session_id):
        collected_info = sessions.get_info(session_id)
        if collected_info:
            collected_info["patient_name"] = (
                collected_info.get("姓名", "")
                or sessions.get_patient_name(session_id)
                or "匿名患者"
            )
        return ChatResponse(
            reply="本次问诊已经完成。如有新的不适，请刷新页面重新开始。",
            table=sessions.get_report(session_id),
            is_complete=True,
            collected_info=collected_info,
        )

    agent = get_agent()

    try:
        config = {"configurable": {"thread_id": session_id}}
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config,
        )
    except Exception as e:
        return ChatResponse(
            reply=f"抱歉，AI老中医此刻有些疲惫，请您稍后再试。（{str(e)}）",
            table=None,
            is_complete=False,
        )

    # 提取 AI 回复
    all_messages = result.get("messages", [])
    reply = extract_last_ai_message(all_messages)

    # 检查是否已完成
    is_complete = sessions.is_complete(session_id)
    report = sessions.get_report(session_id)
    collected_info = sessions.get_info(session_id)

    # 前端兼容：在 collected_info 中附带 patient_name
    if collected_info:
        collected_info["patient_name"] = (
            collected_info.get("姓名", "")
            or sessions.get_patient_name(session_id)
            or "匿名患者"
        )

    return ChatResponse(
        reply=reply,
        table=report,
        is_complete=is_complete,
        collected_info=collected_info if collected_info else None,
    )


async def get_structured_intake(session_id: str):
    return build_patient_state(get_intake_state(session_id))


async def submit_baseline(session_id: str, req: BaselineRequest):
    try:
        return build_patient_state(set_baseline(session_id, req.model_dump()))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def answer_open_intake(session_id: str, req: IntakeOpenAnswerRequest):
    try:
        return build_patient_state(submit_open_answer(session_id, req.answer))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def answer_structured_intake(session_id: str, req: IntakeAnswerRequest):
    try:
        return build_patient_state(submit_intake_answer(
            session_id=session_id,
            question_id=req.question_id,
            option_id=req.option_id,
            note=req.note,
        ))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def move_structured_intake(session_id: str, req: IntakeMoveRequest):
    try:
        return build_patient_state(move_intake(session_id, req.direction))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def complete_structured_intake(session_id: str):
    try:
        return build_patient_state(complete_intake_session(session_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class _UnavailableAgent:
    """AI 不可用时的占位 agent：invoke 立即失败，驱动 process_intake_turn 走确定性离线流程。"""

    def invoke(self, payload, config=None):
        raise RuntimeError("LLM unavailable")


async def analyze_structured_intake(session_id: str):
    try:
        require_baseline_confirmation(session_id)
        internal_state = await asyncio.wait_for(
            asyncio.to_thread(
                process_intake_turn,
                session_id,
                get_analysis_agent(),
            ),
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )
        return build_patient_state(internal_state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError:
        internal_state = await asyncio.to_thread(
            process_intake_turn, session_id, _UnavailableAgent()
        )
        return build_patient_state(internal_state)


async def answer_structured_follow_up(session_id: str, req: IntakeFollowUpRequest):
    try:
        return build_patient_state(submit_follow_up_answer(session_id, req.answer))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def save_record(req: SaveRecordRequest):
    patient_id = req.patient_id
    if _report_repository is not None and _report_repository.get_patient(patient_id) is None:
        raise HTTPException(status_code=404, detail="患者不存在")
    if _report_repository is not None:
        existing_record = _report_repository.get_report_for_session(
            patient_id, req.session_id
        )
    else:
        existing_record = find_record_for_session(
            load_all_records(), patient_id, req.session_id
        )
    if existing_record is not None:
        return {
            "record_id": existing_record["record_id"],
            "patient_name": existing_record.get("patient_name", "匿名患者"),
            "already_saved": True,
        }

    internal_state = get_internal_intake_state(req.session_id)
    readiness = evaluate_patient_readiness(
        internal_state.get("field_states") or {},
        internal_state.get("context") or {},
    )
    if internal_state.get("phase") != "completed" or not readiness["can_complete"]:
        raise HTTPException(
            status_code=400,
            detail="关键资料尚未确认完，暂不能保存。请继续补充问诊；仍不清楚的情况可在线下就医时说明。",
        )
    record_id = str(uuid.uuid4())
    patient_name = req.patient_name or "匿名患者"
    created_at = datetime.now().isoformat()
    doctor_summary = build_doctor_summary(internal_state)
    patient_snapshot = build_patient_state(internal_state)
    data = {
        "record_id": record_id,
        "patient_id": patient_id,
        "session_id": req.session_id,
        "patient_name": patient_name,
        "created_at": created_at,
        "collected_info": {"开放描述": internal_state.get("open_answer", "")} or req.collected_info,
        "structured_answers": req.structured_answers,
        "follow_up_answers": internal_state.get("follow_up_answers") or req.follow_up_answers,
        "markdown_table": internal_state.get("report_markdown") or req.markdown_table,
        "recommended_exams": patient_snapshot.get("recommended_exams") or [],
        "bmi_assessment": patient_snapshot.get("bmi_assessment"),
        "skill_analysis": {"status": "superseded_by_rule_execution"},
        "stop_reason": internal_state.get("stop_reason"),
        "rule_version": doctor_summary["rule_version"],
        "doctor_summary": doctor_summary,
    }
    if _report_repository is not None:
        data = _report_repository.save_report(patient_id, data)
        record_id = data["record_id"]
    else:
        save_record_to_file(record_id, data)
    return {"record_id": record_id, "patient_name": patient_name, "already_saved": False}


async def list_patient_records():
    records = (
        _report_repository.list_patient_reports(DEMO_PATIENT_ID)
        if _report_repository is not None
        else load_all_records()
    )
    return [
        make_history_item(record)
        for record in records
        if belongs_to_patient(record, DEMO_PATIENT_ID)
    ]


async def list_unfinished_intake_sessions():
    if _report_repository is None:
        return []
    return _report_repository.list_unfinished_sessions(DEMO_PATIENT_ID)


async def archive_intake_session(session_id: str):
    if _report_repository is None:
        raise HTTPException(status_code=503, detail="数据库暂不可用")
    try:
        return _report_repository.archive_session(DEMO_PATIENT_ID, session_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="问诊不存在") from error


async def get_patient_record(record_id: str):
    record = (
        _report_repository.get_patient_report(DEMO_PATIENT_ID, record_id)
        if _report_repository is not None
        else load_record(record_id)
    )
    if record is None or not belongs_to_patient(record, DEMO_PATIENT_ID):
        raise HTTPException(status_code=404, detail="记录不存在")
    return make_patient_history_detail(record)


async def delete_patient_record(record_id: str):
    if _report_repository is None:
        raise HTTPException(status_code=503, detail="数据库暂不可用")
    try:
        return _report_repository.soft_delete_report(DEMO_PATIENT_ID, record_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="记录不存在") from error


async def list_records():
    records = (
        _report_repository.list_patient_reports(DEMO_PATIENT_ID)
        if _report_repository is not None
        else load_all_records()
    )
    return [
        {
            "record_id": r["record_id"],
            "patient_name": r.get("patient_name", "匿名"),
            "created_at": r.get("created_at", ""),
            "markdown_table": r.get("markdown_table", ""),
        }
        for r in records
    ]


async def get_record(record_id: str):
    r = (
        _report_repository.get_patient_report(DEMO_PATIENT_ID, record_id)
        if _report_repository is not None
        else load_record(record_id)
    )
    if r is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return r


@app.get("/api/health")
async def health():
    record_count = (
        _report_repository.count_reports()
        if _report_repository is not None
        else len(load_all_records())
    )
    return {
        "status": "ok",
        "framework": "deepagents",
        "records": record_count,
        "database": "ok" if check_database() else "unavailable",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
