"""
AI老中医问诊 - LLM 工厂与诊前完整度分析器

build_llm: 按环境变量选择模型（校内千问 / DeepSeek / 本地 Ollama 三级降级）。
IntakeAnalysisAgent: 把问诊 Skill 作为固定规则注入单次模型调用，做字段证据提取与追问出题。

历史说明：早期版本的 deepagents 十问歌对话链（会话管理器、对话主智能体、
四个辨证子智能体）已随 /api/chat 旧接口一并移除，主线为规则驱动的结构化问诊。
"""
import os
import threading
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# ============================================================
# LLM 工厂
# ============================================================

# 当前生效 LLM 的单次请求超时（秒），由 build_llm 写入
_LLM_TIMEOUT_SECONDS = 0


def build_llm() -> ChatOpenAI:
    """根据环境变量创建 LLM 实例，按优先级降级：
    1. 校内千问（SCHOOL_LLM_API_KEY，校园网内可用，免费）
    2. DeepSeek 云端（DEEPSEEK_API_KEY）
    3. 本地 Ollama（两者都未配置时）
    """
    global _LLM_TIMEOUT_SECONDS
    import httpx

    school_key = os.getenv("SCHOOL_LLM_API_KEY", "")
    if school_key:
        # 校内网关是 OpenAI 兼容接口，但 /v1/chat/completions 不可用，
        # 唯一可用端点是 /api/chat/completions，因此 base_url 以 /api 结尾。
        # 校内 IP 不能走系统代理，必须 trust_env=False 强制直连。
        _LLM_TIMEOUT_SECONDS = 120
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
        # deepseek-v4-flash 同样是推理模型（返回 reasoning_content），
        # max_tokens 太小会被思考过程消耗导致正文截断
        _LLM_TIMEOUT_SECONDS = 60
        return ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.7,
            max_tokens=4096,
            timeout=60,
        )

    _LLM_TIMEOUT_SECONDS = 30
    return ChatOpenAI(
        model="qwen3:8b",
        api_key="ollama",
        base_url="http://localhost:11434/v1",
        temperature=0.7,
        max_tokens=1024,
        timeout=30,
    )


def analysis_timeout_seconds(default: int = 45) -> int:
    """推导主分析流程的超时（秒）。

    一次分析最多包含两段模型调用（提取 + 出题），加上解析开销，
    总超时应跟随当前生效 LLM 的单次超时推导，而不是固定值——
    否则换成推理模型（如校内千问）后会被外层超时强制降级到本地提取器。
    """
    if _LLM_TIMEOUT_SECONDS <= 0:
        build_llm()  # 仅构造客户端实例，不发请求
    return max(default, _LLM_TIMEOUT_SECONDS * 2 + 15)


# ============================================================
# 诊前完整度分析器
# ============================================================

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
