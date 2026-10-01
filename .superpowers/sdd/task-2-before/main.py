"""
中医诊前问诊子智能体 - 后端服务
FastAPI + Deep Agents (LangGraph)
"""
import os
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from agent import (
    create_intake_analysis_agent,
    create_tcm_agent,
    sessions,
)
from intake_flow import (
    complete_intake_session,
    get_internal_intake_state,
    get_intake_state,
    move_intake,
    submit_follow_up_answer,
    submit_intake_answer,
    submit_open_answer,
)
from intake_views import build_doctor_summary, build_patient_state
from skill_analysis import analyze_intake_with_agent, process_intake_turn, unavailable_analysis

load_dotenv()

app = FastAPI(title="AI老中医问诊", version="4.0.0-deepagent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ANALYSIS_TIMEOUT_SECONDS = 45

RECORDS_DIR = Path(__file__).parent / "records"
RECORDS_DIR.mkdir(exist_ok=True)

# 启动时初始化 Agent（全局单例）
_tcm_agent = None
_intake_analysis_agent = None


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
    patient_name: str = ""
    collected_info: dict = Field(default_factory=dict)
    structured_answers: dict = Field(default_factory=dict)
    follow_up_answers: list[dict] = Field(default_factory=list)
    markdown_table: str = ""
    skill_analysis: dict = Field(default_factory=dict)


class IntakeAnswerRequest(BaseModel):
    question_id: str
    option_id: str
    note: str = ""


class IntakeOpenAnswerRequest(BaseModel):
    answer: str


class IntakeMoveRequest(BaseModel):
    direction: str


class IntakeFollowUpRequest(BaseModel):
    answer: str
    question: str = ""
    question_key: str = ""
    question_kind: str = "required"


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

@app.post("/api/chat", response_model=ChatResponse)
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


@app.get("/api/intake/session/{session_id}")
async def get_structured_intake(session_id: str):
    return build_patient_state(get_intake_state(session_id))


@app.post("/api/intake/session/{session_id}/open-answer")
async def answer_open_intake(session_id: str, req: IntakeOpenAnswerRequest):
    try:
        return build_patient_state(submit_open_answer(session_id, req.answer))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/intake/session/{session_id}/doctor-summary")
async def get_doctor_intake_summary(session_id: str):
    return build_doctor_summary(get_intake_state(session_id))


@app.post("/api/intake/session/{session_id}/answer")
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


@app.post("/api/intake/session/{session_id}/move")
async def move_structured_intake(session_id: str, req: IntakeMoveRequest):
    try:
        return build_patient_state(move_intake(session_id, req.direction))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/intake/session/{session_id}/complete")
async def complete_structured_intake(session_id: str):
    return build_patient_state(complete_intake_session(session_id))


@app.post("/api/intake/session/{session_id}/analyze")
async def analyze_structured_intake(session_id: str):
    try:
        internal_state = await asyncio.wait_for(
            asyncio.to_thread(
                process_intake_turn,
                session_id,
                get_analysis_agent(),
            ),
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )
        return build_patient_state(internal_state)
    except TimeoutError:
        state = get_internal_intake_state(session_id)
        state["phase"] = "follow_up"
        state["current_field_key"] = "red_flags"
        state["attempt_number"] = 1
        state["current_question"] = "最近有没有胸痛、明显呼吸困难、晕厥或意识异常？"
        return build_patient_state(get_intake_state(session_id))


@app.post("/api/intake/session/{session_id}/follow-up")
async def answer_structured_follow_up(session_id: str, req: IntakeFollowUpRequest):
    try:
        return build_patient_state(submit_follow_up_answer(session_id, req.answer))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/save_record")
async def save_record(req: SaveRecordRequest):
    record_id = str(uuid.uuid4())
    patient_name = req.patient_name or "匿名患者"
    created_at = datetime.now().isoformat()
    internal_state = get_intake_state(req.session_id)
    doctor_summary = build_doctor_summary(internal_state)
    data = {
        "record_id": record_id,
        "patient_name": patient_name,
        "created_at": created_at,
        "collected_info": {"开放描述": internal_state.get("open_answer", "")} or req.collected_info,
        "structured_answers": req.structured_answers,
        "follow_up_answers": internal_state.get("follow_up_answers") or req.follow_up_answers,
        "markdown_table": internal_state.get("report_markdown") or req.markdown_table,
        "skill_analysis": {"status": "superseded_by_rule_execution"},
        "stop_reason": internal_state.get("stop_reason"),
        "rule_version": doctor_summary["rule_version"],
        "doctor_summary": doctor_summary,
    }
    save_record_to_file(record_id, data)
    return {"record_id": record_id, "patient_name": patient_name}


@app.get("/api/records")
async def list_records():
    records = load_all_records()
    return [
        {
            "record_id": r["record_id"],
            "patient_name": r.get("patient_name", "匿名"),
            "created_at": r.get("created_at", ""),
            "markdown_table": r.get("markdown_table", ""),
        }
        for r in records
    ]


@app.get("/api/records/{record_id}")
async def get_record(record_id: str):
    r = load_record(record_id)
    if r is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return r


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "framework": "deepagents",
        "records": len(load_all_records()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


