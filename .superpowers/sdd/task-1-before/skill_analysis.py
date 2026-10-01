from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage

from follow_up_policy import apply_follow_up_policy
from exam_recommendations import build_recommended_exams
from intake_execution import calculate_execution, merge_field_updates
from intake_question_policy import decide_stop, question_for_field
from obesity_intake_schema import FIELD_DEFINITIONS, get_field_definition


DISCLAIMER = "本结果仅用于诊前信息整理和检查准备，不能替代医生诊断、检查决策或治疗。"
PAUSE_INTAKE_PHRASES = ("暂停本次", "暂停问诊", "结束本次问诊", "结束问诊", "停止问诊")
LOCAL_RED_FLAG_MARKERS = {
    "胸痛": ("胸痛",),
    "明显呼吸困难": ("明显呼吸困难", "呼吸困难", "喘不上气", "喘不过气"),
    "晕厥": ("晕厥", "晕倒"),
    "意识异常": ("意识异常", "意识不清"),
}
RED_FLAG_NEGATIONS = ("没有", "没出现", "未出现", "无", "否认", "从未", "不伴")
RED_FLAG_ASSERTION_RESETS = ("但是", "但", "后来", "随后", "又有", "仍有", "出现", "发生")


def build_extraction_prompt(state: dict[str, Any]) -> str:
    registry = [
        {
            "field_key": item.key,
            "section": item.section,
            "group": item.group,
            "source": item.source,
        }
        for item in FIELD_DEFINITIONS
    ]
    payload = {
        "open_answer": state.get("open_answer", ""),
        "follow_up_answers": state.get("follow_up_answers") or [],
        "latest_answer": state.get("latest_answer", ""),
        "field_registry": registry,
    }
    return f"""你是成人单纯性肥胖诊前问诊的信息提取器。

必须参考 tcm-intake-checklist Skill，把患者原话映射到给定字段。
- 只提取患者已经明确表达的信息，不猜测。
- 不输出证型、诊断、处方或患病概率。
- 不得计算执行度、分项分数或停止结论。
- status 只能是 confirmed、partial、unavailable。
- evidence 必须保留简短患者原话。
- 发现前后矛盾时写入 conflicts，并在对应字段更新中设置 conflict=true。
- 发现胸痛、明显呼吸困难、晕厥、意识异常等危险表现时写入 red_flags。
- 只输出 JSON，不要输出 Markdown。

输出格式：
{{
  "field_updates": [
    {{"field_key": "字段 key", "status": "confirmed|partial|unavailable", "evidence": "患者原话", "confidence": 0.0, "conflict": false}}
  ],
  "conflicts": [{{"field_key": "字段 key", "description": "矛盾说明"}}],
  "red_flags": ["危险表现"]
}}

输入资料：
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def build_question_prompt(field_key: str, attempt_number: int, state: dict[str, Any]) -> str:
    definition = get_field_definition(field_key)
    payload = {
        "field_key": field_key,
        "field_group": definition.group,
        "attempt_number": attempt_number,
        "default_question": definition.question,
        "retry_question": definition.retry_question,
        "open_answer": state.get("open_answer", ""),
        "follow_up_answers": state.get("follow_up_answers") or [],
    }
    return f"""必须参考 tcm-questioning-guide Skill，为患者生成当前一个追问。

- 一次只问一个信息点。
- 使用自然、温和、日常语言，不暴露 field_key、执行度、缺失项或内部判断。
- attempt_number=2 时，承接患者刚才可能不容易判断的情况，只委婉确认一次，并提供少量具体选项。
- 危险表现由界面持续提醒，但不得要求患者暂停或结束问诊；仍需围绕当前字段提出可回答的问题。
- 不输出证型、诊断、处方或检查结论。
- 只输出 JSON：{{"question":"问题文本"}}

输入资料：
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def parse_extraction_response(text: str) -> dict[str, Any]:
    try:
        data = _extract_json(text)
    except (json.JSONDecodeError, ValueError, TypeError):
        return {"status": "unavailable", "field_updates": [], "conflicts": [], "red_flags": []}

    known_keys = {item.key for item in FIELD_DEFINITIONS}
    updates = []
    for item in data.get("field_updates") or []:
        if not isinstance(item, dict):
            continue
        field_key = str(item.get("field_key", "")).strip()
        if field_key not in known_keys:
            continue
        status = str(item.get("status", "partial")).strip().lower()
        if status not in {"confirmed", "partial", "unavailable"}:
            status = "partial"
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0
        updates.append({
            "field_key": field_key,
            "status": status,
            "evidence": str(item.get("evidence", "")).strip(),
            "confidence": confidence,
            "conflict": bool(item.get("conflict")),
        })
    conflicts = [item for item in (data.get("conflicts") or []) if isinstance(item, dict)]
    return {
        "status": "completed",
        "field_updates": updates,
        "conflicts": conflicts,
        "red_flags": _string_list(data.get("red_flags")),
    }


def parse_question_response(text: str, fallback_question: str) -> str:
    try:
        data = _extract_json(text)
    except (json.JSONDecodeError, ValueError, TypeError):
        return fallback_question
    question = str(data.get("question", "")).strip()
    if any(phrase in question for phrase in PAUSE_INTAKE_PHRASES):
        return fallback_question
    return question or fallback_question


def extract_local_basic_fields(text: str) -> list[dict[str, Any]]:
    clean = str(text or "").strip()
    if not clean:
        return []
    updates = []
    if any(marker in clean for marker in ("想减重", "希望减重", "控制体重", "改善体重", "减肥")):
        updates.append({
            "field_key": "main_goal", "status": "confirmed", "evidence": clean, "confidence": 1.0,
        })
    height_weight = re.search(
        r"身高\s*(\d{2,3}(?:\.\d+)?)\s*(?:厘米|cm|CM)?[^。；]{0,24}?体重\s*(\d{2,3}(?:\.\d+)?)\s*(?:公斤|千克|kg|KG|斤)?",
        clean,
    )
    if height_weight:
        updates.append({
            "field_key": "height_weight",
            "status": "confirmed",
            "evidence": height_weight.group(0),
            "confidence": 1.0,
        })
    weight_change = re.search(r"(?:近|最近|这)?[^，。；]{0,12}(?:体重)?(?:增加|上涨|上升|下降|减轻|胖了|瘦了)[^，。；]{0,12}", clean)
    if weight_change:
        updates.append({
            "field_key": "weight_change",
            "status": "confirmed",
            "evidence": weight_change.group(0),
            "confidence": 1.0,
        })
    return updates


def extract_local_red_flags(text: str) -> list[str]:
    clean = str(text or "").strip()
    detected = []
    for label, markers in LOCAL_RED_FLAG_MARKERS.items():
        found = False
        for marker in markers:
            start = 0
            while True:
                index = clean.find(marker, start)
                if index < 0:
                    break
                prefix = clean[max(0, index - 32):index]
                last_negation = max((prefix.rfind(item) for item in RED_FLAG_NEGATIONS), default=-1)
                last_reset = max((prefix.rfind(item) for item in RED_FLAG_ASSERTION_RESETS), default=-1)
                if last_negation <= last_reset:
                    found = True
                    break
                start = index + len(marker)
            if found:
                detected.append(label)
                break
    return detected


def _agent_content(agent: Any, prompt: str, thread_id: str) -> str:
    result = agent.invoke(
        {"messages": [HumanMessage(content=prompt)]},
        {"configurable": {"thread_id": thread_id}},
    )
    return _last_ai_content(result)


def extract_fields_with_agent(session_id: str, state: dict[str, Any], agent: Any) -> dict[str, Any]:
    try:
        content = _agent_content(
            agent,
            build_extraction_prompt(state),
            f"obesity-extraction-{session_id}-{state.get('turn', 0)}",
        )
        return parse_extraction_response(content)
    except Exception:
        return {"status": "unavailable", "field_updates": [], "conflicts": [], "red_flags": []}


def generate_question_with_agent(
    session_id: str,
    field_key: str,
    attempt_number: int,
    state: dict[str, Any],
    agent: Any,
) -> str:
    fallback = question_for_field(field_key, attempt_number)
    try:
        content = _agent_content(
            agent,
            build_question_prompt(field_key, attempt_number, state),
            f"obesity-question-{session_id}-{state.get('turn', 0)}",
        )
        return parse_question_response(content, fallback)
    except Exception:
        return fallback


def enforce_attempt_status(
    updates: list[dict[str, Any]],
    field_states: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep retry limits under server control instead of trusting model status."""
    normalized: list[dict[str, Any]] = []
    for item in updates:
        update = dict(item)
        field_key = update.get("field_key")
        attempts = int((field_states.get(field_key) or {}).get("attempts") or 0)
        if update.get("status") == "unavailable" and attempts < 2:
            update["status"] = "partial"
        normalized.append(update)
    return normalized


def confirm_detected_red_flags(
    updates: list[dict[str, Any]],
    red_flags: list[str],
) -> list[dict[str, Any]]:
    if not red_flags:
        return updates

    evidence = "、".join(dict.fromkeys(red_flags))
    normalized = [dict(item) for item in updates]
    for update in normalized:
        if update.get("field_key") == "red_flags":
            update.update({
                "status": "confirmed",
                "evidence": evidence,
                "confidence": max(float(update.get("confidence") or 0), 0.99),
                "conflict": False,
            })
            return normalized

    normalized.append({
        "field_key": "red_flags",
        "status": "confirmed",
        "evidence": evidence,
        "confidence": 0.99,
        "conflict": False,
    })
    return normalized


def process_intake_turn(session_id: str, agent: Any) -> dict[str, Any]:
    from intake_flow import apply_analysis_turn, get_internal_intake_state

    state = get_internal_intake_state(session_id)
    extraction = extract_fields_with_agent(session_id, state, agent)
    ai_available = extraction.get("status") == "completed"
    local_red_flags = extract_local_red_flags(
        state.get("latest_answer") or state.get("open_answer", "")
    )
    extraction["red_flags"] = list(dict.fromkeys([
        *(extraction.get("red_flags") or []),
        *local_red_flags,
    ]))

    if not ai_available and state.get("follow_up_answers"):
        latest = state["follow_up_answers"][-1]
        if latest.get("answer_quality") == "provided" and latest.get("question_key"):
            extraction["field_updates"] = [{
                "field_key": latest["question_key"],
                "status": "confirmed",
                "evidence": latest.get("answer", ""),
                "confidence": 1.0,
            }]
    if not ai_available:
        local_updates = extract_local_basic_fields(state.get("open_answer", ""))
        existing_keys = {item.get("field_key") for item in extraction.get("field_updates") or []}
        extraction["field_updates"].extend(
            item for item in local_updates if item["field_key"] not in existing_keys
        )

    extraction["field_updates"] = confirm_detected_red_flags(
        extraction.get("field_updates") or [],
        extraction.get("red_flags") or [],
    )
    extraction["field_updates"] = enforce_attempt_status(
        extraction["field_updates"],
        state["field_states"],
    )
    known_red_flags = list(dict.fromkeys([
        *(state.get("safety_alerts") or []),
        *(extraction.get("red_flags") or []),
    ]))
    extraction["red_flags"] = known_red_flags

    prospective_states = merge_field_updates(
        state["field_states"],
        extraction.get("field_updates") or [],
        state.get("turn", 0),
    )
    execution = calculate_execution(prospective_states, state.get("context") or {})
    decision = decide_stop(
        prospective_states,
        execution,
        state.get("follow_up_answers") or [],
        state.get("context") or {},
        red_flags=known_red_flags,
        ai_available=ai_available,
    )

    question = ""
    attempt_number = 0
    recommended_exams = []
    if not decision.get("stop"):
        field_key = decision["next_field_key"]
        previous_attempts = sum(
            1 for item in state.get("follow_up_answers") or []
            if item.get("question_key") == field_key
        )
        attempt_number = previous_attempts + 1
        if ai_available:
            question = generate_question_with_agent(session_id, field_key, attempt_number, state, agent)
        else:
            question = question_for_field(field_key, attempt_number)
    else:
        recommended_exams = build_recommended_exams(
            prospective_states,
            red_flags=known_red_flags,
        )

    return apply_analysis_turn(
        session_id,
        extraction=extraction,
        decision=decision,
        question=question,
        attempt_number=attempt_number,
        recommended_exams=recommended_exams,
    )


def unavailable_analysis(message: str = "智能完整度分析暂不可用，基础档案已正常生成。") -> dict[str, Any]:
    return {
        "status": "unavailable",
        "completeness_status": "unknown",
        "completeness_summary": "",
        "missing_required_items": [],
        "optional_items": [],
        "follow_up_key": "",
        "follow_up_kind": "required",
        "follow_up_questions": [],
        "safety_alerts": [],
        "recommended_exams": [],
        "disclaimer": DISCLAIMER,
        "message": message,
    }


def build_analysis_prompt(state: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "summary": state.get("summary") or {},
            "structured_answers": state.get("answers") or {},
            "follow_up_answers": state.get("follow_up_answers") or [],
            "follow_up_count": state.get("follow_up_count", 0),
        },
        ensure_ascii=False,
        indent=2,
    )
    return f"""请检查下面这份中医诊前问诊资料是否足以支持后续诊中信息判断和医生开方前的信息准备。

必须按需查阅并使用项目中的两个 Skill：
1. tcm-intake-checklist：根据十问歌、主诉和老中医问诊经验，确认基础必问项、条件选问项和缺失信息。
2. tcm-questioning-guide：把当前最重要的一个缺失信息转换为自然、温和、单一问点的补问问题。

任务要求：
- 不做中医辨证，不输出证型、诊断、处方、药物剂量或针灸方案。
- 固定题目答完不等于信息完整，必须按十问歌、主诉特点和老中医问诊经验判断。
- 只有缺失的关键必问项可以令 completeness_status 为 needs_follow_up；建议选问项不能阻止流程结束。
- 已在 follow_up_answers 中出现过的 question_key 代表该缺口已经尝试询问，即使回答“不知道”也不得再次追问或更换说法追问。
- follow_up_questions 最多输出一个补问问题；每轮收到回答后重新判断资料是否够用，仍缺影响后续判断且尚未询问的关键必问项时输出一个自然问题，信息足够或只剩选问项时输出空数组。
- 每个追问必须给出稳定的英文蛇形 question_key；同一信息缺口在不同轮次、不同问法下必须使用同一个 key。
- 仍缺关键必问信息时，除危险信号相关项目外，暂不推荐一般检查。
- 信息充分后，仅推荐与主诉或已知风险直接相关的检查，不得照搬体检套餐。
- 每个检查写明检查方式、建议科室、临床意义、优先级和检查前注意事项；不输出价格。
- 危险信号放入 safety_alerts，并明确建议及时线下就医。
- 只输出 JSON，不要使用 Markdown 代码块，不添加 JSON 之外的文字。

输出格式：
{{
  "completeness_status": "complete|needs_follow_up",
  "completeness_summary": "完整度判断及依据",
  "missing_required_items": ["缺失的必问信息"],
  "optional_items": ["根据主诉建议补充的选问信息"],
  "follow_up_key": "当前追问对应的稳定英文蛇形 key，无追问则为空字符串",
  "follow_up_kind": "required|optional，无追问时填写 required",
  "follow_up_questions": ["最多一个、一次只包含一个问点的自然问题"],
  "safety_alerts": ["必要的安全提示"],
  "recommended_exams": [
    {{
      "name": "检查项目",
      "type": "抽血|仪器|影像|其他",
      "department": "建议就诊或检查科室",
      "reason": "与当前主诉相关的临床意义",
      "priority": "urgent|priority|routine",
      "precautions": "检查前注意事项，无则留空"
    }}
  ]
}}

问诊资料：
{payload}
"""


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("analysis result must be an object")
    return value


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_exams(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    exams = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        priority = str(item.get("priority", "routine")).lower()
        if priority not in {"urgent", "priority", "routine"}:
            priority = "routine"
        exams.append({
            "name": name,
            "type": str(item.get("type", "其他")).strip() or "其他",
            "department": str(item.get("department", "由医生确定")).strip() or "由医生确定",
            "reason": str(item.get("reason", "")).strip(),
            "priority": priority,
            "precautions": str(item.get("precautions", "")).strip(),
        })
    return exams


def parse_analysis_response(text: str) -> dict[str, Any]:
    try:
        data = _extract_json(text)
    except (json.JSONDecodeError, ValueError, TypeError):
        return unavailable_analysis()

    completeness_status = str(data.get("completeness_status", "needs_follow_up")).lower()
    if completeness_status not in {"complete", "needs_follow_up"}:
        completeness_status = "needs_follow_up"

    return {
        "status": "completed",
        "completeness_status": completeness_status,
        "completeness_summary": str(data.get("completeness_summary", "")).strip(),
        "missing_required_items": _string_list(data.get("missing_required_items")),
        "optional_items": _string_list(data.get("optional_items")),
        "follow_up_key": str(data.get("follow_up_key", "")).strip(),
        "follow_up_kind": str(data.get("follow_up_kind", "required")).strip().lower(),
        "follow_up_questions": _string_list(data.get("follow_up_questions"))[:1],
        "safety_alerts": _string_list(data.get("safety_alerts")),
        "recommended_exams": _normalize_exams(data.get("recommended_exams")),
        "disclaimer": DISCLAIMER,
        "message": "",
    }


def _last_ai_content(result: dict[str, Any]) -> str:
    for message in reversed(result.get("messages", [])):
        if getattr(message, "type", None) == "ai" and getattr(message, "content", None):
            return str(message.content)
    return ""


def analyze_intake_with_agent(session_id: str, state: dict[str, Any], agent: Any) -> dict[str, Any]:
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=build_analysis_prompt(state))]},
            {"configurable": {"thread_id": f"structured-analysis-{session_id}"}},
        )
        analysis = parse_analysis_response(_last_ai_content(result))
        return apply_follow_up_policy(analysis, state)
    except Exception:
        return unavailable_analysis()
