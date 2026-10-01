"""
AI老中医问诊 - Deep Agent 配置
基于 deepagents 框架的中医诊前问诊智能体
"""
import os
import json
import threading
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent
from deepagents.middleware.subagents import SubAgent

# ============================================================
# 会话状态管理（线程安全）
# ============================================================

class SessionManager:
    """跨请求的会话状态存储"""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, dict] = {}

    def get(self, session_id: str) -> dict:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "info": {},
                    "complete": False,
                    "report": None,
                    "patient_name": "",
                }
            return dict(self._sessions[session_id])

    def record(self, session_id: str, topic: str, answer: str):
        with self._lock:
            s = self._sessions.setdefault(
                session_id,
                {"info": {}, "complete": False, "report": None, "patient_name": ""},
            )
            s["info"][topic] = answer
            if topic == "姓名":
                s["patient_name"] = answer

    def complete(self, session_id: str, report: str):
        with self._lock:
            s = self._sessions.setdefault(
                session_id,
                {"info": {}, "complete": False, "report": None, "patient_name": ""},
            )
            s["complete"] = True
            s["report"] = report

    def is_complete(self, session_id: str) -> bool:
        return self._sessions.get(session_id, {}).get("complete", False)

    def get_report(self, session_id: str) -> Optional[str]:
        return self._sessions.get(session_id, {}).get("report")

    def get_info(self, session_id: str) -> dict:
        return dict(self._sessions.get(session_id, {}).get("info", {}))

    def get_patient_name(self, session_id: str) -> str:
        return self._sessions.get(session_id, {}).get("patient_name", "")


# 全局会话管理器
sessions = SessionManager()


# ============================================================
# LLM 工厂
# ============================================================

def build_llm() -> ChatOpenAI:
    """根据环境变量创建 LLM 实例，按优先级降级：
    1. 校内千问（SCHOOL_LLM_API_KEY，校园网内可用，免费）
    2. DeepSeek 云端（DEEPSEEK_API_KEY）
    3. 本地 Ollama（两者都未配置时）
    """
    import httpx

    school_key = os.getenv("SCHOOL_LLM_API_KEY", "")
    if school_key:
        # 校内网关是 OpenAI 兼容接口，但 /v1/chat/completions 不可用，
        # 唯一可用端点是 /api/chat/completions，因此 base_url 以 /api 结尾。
        # 校内 IP 不能走系统代理，必须 trust_env=False 强制直连。
        return ChatOpenAI(
            model=os.getenv("SCHOOL_LLM_MODEL", "vllm.Qwen3.8-27B"),
            api_key=school_key,
            base_url=os.getenv("SCHOOL_LLM_BASE_URL", "http://59.69.101.206:3000/api"),
            temperature=0.7,
            # 该模型为推理模型（思考过程消耗 token），max_tokens 太小会截断正文
            max_tokens=4096,
            timeout=120,
            http_client=httpx.Client(trust_env=False, timeout=120),
        )

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if api_key:
        return ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.7,
            max_tokens=1024,
            timeout=30,
        )

    return ChatOpenAI(
        model="qwen3:8b",
        api_key="ollama",
        base_url="http://localhost:11434/v1",
        temperature=0.7,
        max_tokens=1024,
        timeout=30,
    )


# ============================================================
# 自定义工具
# ============================================================

@tool
def record_patient_info(topic: str, answer: str, config: RunnableConfig) -> str:
    """记录患者对某个问诊主题的回答。

    Args:
        topic: 问诊主题名称，如 "主诉"、"寒热"、"汗出"、"头身"、
               "二便"、"饮食"、"胸腹"、"睡眠"、"口渴"、"旧病"、"病因"、"姓名"
        answer: 患者对该主题的回答内容
    """
    sid = config.get("configurable", {}).get("thread_id", "")
    if not sid:
        return "错误：无法确定当前会话。"
    sessions.record(sid, topic, answer)
    return f"已记录「{topic}」: {answer}"


@tool
def get_collected_info(config: RunnableConfig) -> str:
    """获取当前已采集的所有患者信息，以 JSON 格式返回。"""
    sid = config.get("configurable", {}).get("thread_id", "")
    if not sid:
        return json.dumps({"error": "无法确定当前会话"}, ensure_ascii=False)
    info = sessions.get_info(sid)
    return json.dumps(info, ensure_ascii=False, indent=2) if info else "（尚无记录）"


@tool
def complete_intake(report_markdown: str, config: RunnableConfig) -> str:
    """完成问诊，保存最终的四诊档案。调用此工具后问诊正式结束。

    Args:
        report_markdown: 完整的四诊档案 Markdown 表格，
            格式为 "| 四诊项目 | 详情 |\n|---------|------|\n| ... | ... |"
    """
    sid = config.get("configurable", {}).get("thread_id", "")
    if not sid:
        return "错误：无法确定当前会话。"
    sessions.complete(sid, report_markdown)
    return "四诊档案已生成，问诊结束。感谢您的配合！"


# ============================================================
# TCM 辨证子智能体（4 个并行分析视角）
# ============================================================

TCM_SUBAGENTS: list[SubAgent] = [
    {
        "name": "bagang-analyzer",
        "description": (
            "八纲辨证分析：从阴阳、表里、寒热、虚实八个纲领入手，"
            "判断患者的整体证候倾向。当需要判定病性（寒热虚实）"
            "和病位（表里）时调用此子智能体。"
        ),
        "system_prompt": (
            "你是中医八纲辨证专家。你会收到患者当前已采集的四诊信息（JSON 格式）。\n\n"
            "请从以下四个维度给出简洁专业的分析：\n"
            "1. **阴阳归类**：整体偏阴证还是阳证？关键依据是什么？\n"
            "2. **表里判断**：病位在表、在里、还是半表半里？有何表现支持？\n"
            "3. **寒热定性**：偏寒还是偏热？具体在哪些症候上体现？\n"
            "4. **虚实定性**：属虚证、实证还是虚实夹杂？依据是什么？\n\n"
            "最后，提出 1-2 个你认为了解还不够、需要进一步向患者追问的方向。\n\n"
            "输出控制在 200 字以内，直接给出分析，不要客套话。"
        ),
    },
    {
        "name": "zangfu-analyzer",
        "description": (
            "脏腑辨证分析：从五脏六腑的功能状态和相互关系分析病情。"
            "当需要判断病变涉及的脏腑及其传变规律时调用此子智能体。"
        ),
        "system_prompt": (
            "你是中医脏腑辨证专家。你会收到患者当前已采集的四诊信息（JSON 格式）。\n\n"
            "请从以下角度给出简洁专业的分析：\n"
            "1. **受累脏腑**：哪些脏腑可能受累（心、肝、脾、肺、肾、胃、胆、大肠、小肠、膀胱等）？\n"
            "2. **传变关系**：是否存在脏腑之间的传变（如肝木克脾土、心肾不交等）？\n"
            "3. **功能失调**：受累脏腑的功能出现了什么偏差？\n\n"
            "最后，提出 1-2 个需要进一步追问的方向。\n\n"
            "输出控制在 200 字以内，直接给出分析，不要客套话。"
        ),
    },
    {
        "name": "qixue-analyzer",
        "description": (
            "气血津液分析：从气、血、津液的生成、运行、代谢角度分析病情。"
            "当需要判断气虚气滞、血虚血瘀、痰湿水饮等情况时调用。"
        ),
        "system_prompt": (
            "你是中医气血津液专家。你会收到患者当前已采集的四诊信息（JSON 格式）。\n\n"
            "请从以下角度给出简洁专业的分析：\n"
            "1. **气机状态**：有无气虚、气滞、气逆？具体表现是什么？\n"
            "2. **血分状态**：有无血虚、血瘀、血热？有什么症状支持？\n"
            "3. **津液状态**：有无津亏、痰湿、水饮？体现在哪些方面？\n\n"
            "最后，提出 1-2 个需要进一步追问的方向。\n\n"
            "输出控制在 200 字以内，直接给出分析，不要客套话。"
        ),
    },
    {
        "name": "bingyin-analyzer",
        "description": (
            "病因病机分析：从外感六淫、内伤七情、饮食劳倦等角度推断病因和核心病机。"
            "当需要判断发病原因和病理机制时调用。"
        ),
        "system_prompt": (
            "你是中医病因病机专家。你会收到患者当前已采集的四诊信息（JSON 格式）。\n\n"
            "请从以下角度给出简洁专业的分析：\n"
            "1. **外感因素**：六淫（风、寒、暑、湿、燥、火）中哪些可能参与？\n"
            "2. **内伤因素**：七情（喜、怒、忧、思、悲、恐、惊）有无影响？\n"
            "3. **生活因素**：饮食、劳倦、作息等有无关联？\n"
            "4. **核心病机**：用一两句话概括当前最核心的病机。\n\n"
            "最后，提出 1-2 个需要进一步追问的方向。\n\n"
            "输出控制在 200 字以内，直接给出分析，不要客套话。"
        ),
    },
]

# ============================================================
# 主 Agent 系统提示词
# ============================================================

SYSTEM_PROMPT = """你是"AI老中医问诊助手"——一位经验丰富的中医诊前问诊智能体。

## 核心职责
按照中医"十问歌"框架，与患者进行自然对话，逐步采集信息，最终生成"📜 四诊档案"。

## 必须执行的工作流程

### 初始化（收到患者首条消息后立即执行）
1. 使用 write_todos 创建以下 12 项待办清单：
   问姓名、问主诉、问寒热、问汗出、问头身、问二便、
   问饮食、问胸腹、问睡眠、问口渴、问旧病、问病因

### 每轮对话（每次收到患者回复后必须执行）
1. **必须调用** record_patient_info(topic="当前主题名", answer="患者回答的原文摘要") 记录信息
2. 更新 write_todos 中对应主题为 completed
3. 选择下一个信息不足的主题，准备提问

### 辨证分析（按需使用，非必须每轮都做）
当已采集了 3 个以上主题的信息后，可以同时派出 4 位辨证专家并行分析：
- task(subagent_type="bagang-analyzer", ...)
- task(subagent_type="zangfu-analyzer", ...)
- task(subagent_type="qixue-analyzer", ...)
- task(subagent_type="bingyin-analyzer", ...)
用专家分析来指导后续追问方向。信息不足时不必强行调用。

## 铁律

### 一次只问一个问题
每条回复中**只能包含一个问句**。绝对禁止在一个回复中塞入多个问题。
❌ 错误：「头是怎么痛的？什么时候发作？有没有诱因？」
✅ 正确：「您这个头痛，具体是什么感觉呢？是胀痛还是刺痛？」

### 回复风格
- 每条回复 2-4 句话，简洁温和
- 不要使用 Markdown 格式（**、列表等），纯文本即可
- 自称"您的老中医助手"，称呼对方"您"
- **严禁出现**：AI、机器人、大模型、智能体、算法、系统、工具、调用、记录 等字眼

### 问诊顺序
按十问歌顺序自然推进：姓名→主诉→寒热→汗出→头身→二便→饮食→胸腹→睡眠→口渴→旧病→病因
如果患者已回答清楚某主题，可以跳过。

## 结束条件
当 12 个主题全部采集完毕：
1. 调用 get_collected_info() 获取全部信息
2. 生成如下四诊档案 Markdown 表格：

| 四诊项目 | 详情 |
|---------|------|
| 姓名 | ... |
| 主诉 | ... |
| 寒热 | ... |
| 汗出 | ... |
| 头身 | ... |
| 二便 | ... |
| 饮食 | ... |
| 胸腹 | ... |
| 睡眠 | ... |
| 口渴 | ... |
| 旧病 | ... |
| 病因 | ... |
| 服药情况 | （如有则填写） |
| 舌象 | 待面诊采集 |
| 脉象 | 待面诊采集 |

3. 调用 complete_intake(report_markdown="上述完整的 Markdown 表格")
4. 以温暖话语告知患者问诊结束"""


# ============================================================
# Agent 工厂
# ============================================================

# 全局单例
_tcm_agent = None
_agent_lock = threading.Lock()


def create_tcm_agent():
    """创建并返回 AI老中医问诊 Deep Agent（单例）。"""
    global _tcm_agent
    if _tcm_agent is not None:
        return _tcm_agent

    with _agent_lock:
        if _tcm_agent is not None:
            return _tcm_agent

        llm = build_llm()
        checkpointer = MemorySaver()

        # Skills 目录 — 按需加载的中医知识库
        import pathlib
        _skills_dir = pathlib.Path(__file__).parent / "skills"
        skill_paths = [
            str(_skills_dir / "tcm-intake-checklist"),
            str(_skills_dir / "tcm-questioning-guide"),
        ]

        _tcm_agent = create_deep_agent(
            model=llm,
            tools=[record_patient_info, get_collected_info, complete_intake],
            system_prompt=SYSTEM_PROMPT,
            skills=skill_paths,
            checkpointer=checkpointer,
        )
        return _tcm_agent


ANALYSIS_SYSTEM_PROMPT = """你是中医诊前资料完整度审核助手，不与患者进行闲聊问诊。

你的唯一任务是审核用户提供的结构化问诊资料，并严格按照用户指定的 JSON 格式返回结果。
必须按需读取 tcm-intake-checklist 和 tcm-questioning-guide 两个 Skill：前者决定必问项、选问项和完整度，后者只生成当前最重要的一个补问问题。

不得执行旧的十二步对话问诊流程，不得询问姓名，不得调用患者信息记录工具。
不得辨证、不得输出证型、诊断、处方、药物剂量或针灸方案。
除 Skill 文件读取所需的内部操作外，最终回复只能包含 JSON。"""

class IntakeAnalysisAgent:
    """把两个 Skill 作为固定规则注入单次模型调用，避免工具循环卡住。"""

    def __init__(self, llm=None):
        self.llm = llm or build_llm()
        skills_dir = Path(__file__).parent / "skills"
        skill_contents = [
            (skills_dir / "tcm-intake-checklist" / "SKILL.md").read_text(encoding="utf-8-sig"),
            (skills_dir / "tcm-questioning-guide" / "SKILL.md").read_text(encoding="utf-8-sig"),
        ]
        self.system_prompt = ANALYSIS_SYSTEM_PROMPT + "\n\n以下是必须执行的两个 Skill：\n\n" + "\n\n".join(skill_contents)

    def invoke(self, payload, config=None):
        response = self.llm.invoke(
            [SystemMessage(content=self.system_prompt), *payload.get("messages", [])],
            config=config,
        )
        return {"messages": [response]}


_analysis_agent = None
_analysis_agent_lock = threading.Lock()


def create_intake_analysis_agent():
    """创建并缓存独立的诊前完整度分析器。"""
    global _analysis_agent
    if _analysis_agent is not None:
        return _analysis_agent

    with _analysis_agent_lock:
        if _analysis_agent is None:
            _analysis_agent = IntakeAnalysisAgent()
        return _analysis_agent
