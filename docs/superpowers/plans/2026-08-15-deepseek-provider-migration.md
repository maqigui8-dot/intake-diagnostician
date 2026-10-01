# DeepSeek 模型接入替换实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将后端云端大模型从千问替换为 DeepSeek V4 Flash，并保留本地 Ollama 回退。

**Architecture:** 继续使用现有 `ChatOpenAI` 的 OpenAI 兼容能力，只修改 `build_llm()` 的云端配置来源。业务层、两个 Skill、问诊状态机和前端接口保持不变。

**Tech Stack:** Python 3.14、LangChain `ChatOpenAI`、python-dotenv、DeepSeek OpenAI-compatible API、Python `unittest`

## Global Constraints

- 真实 API 密钥只允许写入 `backend/.env`。
- 源码、测试、README 和设计文档不得包含真实密钥。
- 云端模型固定为 `deepseek-v4-flash`，接口地址固定为 `https://api.deepseek.com`。
- 未配置 `DEEPSEEK_API_KEY` 时保留本地 Ollama `qwen3:8b` 回退。
- 不改变患者问诊流程、执行度计分或追问策略。
- 当前目录没有 Git 元数据，不初始化 Git，不伪造提交。

---

### Task 1: 用测试锁定 DeepSeek 与 Ollama 模型选择

**Files:**
- Modify: `backend/tests/test_skill_analysis.py`
- Modify: `backend/agent.py`

**Interfaces:**
- Consumes: `agent.build_llm() -> ChatOpenAI`
- Produces: 根据 `DEEPSEEK_API_KEY` 选择 DeepSeek 或 Ollama 的确定性模型工厂

- [ ] **Step 1: 写 DeepSeek 云端配置失败测试**

通过 `patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}, clear=True)` 调用 `build_llm()`，断言模型名为 `deepseek-v4-flash`、接口地址为 `https://api.deepseek.com`，并确认不读取 `DASHSCOPE_API_KEY`。

- [ ] **Step 2: 运行定向测试确认失败**

Run: `python -m unittest tests.test_skill_analysis.ModelConfigurationTests -v`

Expected: 因当前仍使用千问变量和 `qwen-plus` 而失败。

- [ ] **Step 3: 最小修改模型工厂**

将 `build_llm()` 云端分支改为读取 `DEEPSEEK_API_KEY`，使用 `deepseek-v4-flash` 和 `https://api.deepseek.com`；保留原 Ollama 分支。

- [ ] **Step 4: 增加并通过 Ollama 回退测试**

在清空环境变量时调用 `build_llm()`，断言模型名为 `qwen3:8b`，接口地址为 `http://localhost:11434/v1`。

Run: `python -m unittest tests.test_skill_analysis.ModelConfigurationTests -v`

Expected: DeepSeek 和 Ollama 两项模型配置测试全部通过。

### Task 2: 更新安全配置和项目说明

**Files:**
- Modify: `backend/.env`
- Modify: `README.md`

**Interfaces:**
- Consumes: 用户提供的 DeepSeek API 密钥
- Produces: 本地 `DEEPSEEK_API_KEY` 配置和不含真实密钥的运行说明

- [ ] **Step 1: 替换本地环境变量**

删除 `backend/.env` 中的 `DASHSCOPE_API_KEY`，只写入一行 `DEEPSEEK_API_KEY=<用户提供的密钥>`。

- [ ] **Step 2: 更新 README**

将千问云端说明替换为 DeepSeek V4 Flash，示例变量写作 `DEEPSEEK_API_KEY="your-api-key-here"`；保留 Ollama 回退说明。

- [ ] **Step 3: 执行密钥泄漏检查**

Run: `rg -n "sk-d82|DASHSCOPE_API_KEY|dashscope.aliyuncs.com|qwen-plus" backend README.md -g "!backend/.env"`

Expected: 无真实密钥、旧变量、旧地址或旧云端模型残留。

### Task 3: 全量验证并重启服务

**Files:**
- Test: `backend/tests/*.py`
- Test: `frontend/tests/*.test.mjs`

**Interfaces:**
- Consumes: 完成替换后的后端配置
- Produces: 可运行的 DeepSeek 问诊服务

- [ ] **Step 1: 运行后端全量测试**

Run: `python -m unittest discover -s tests -v`

Expected: 全部测试通过。

- [ ] **Step 2: 运行前端测试与构建**

Run: `npm.cmd test`

Expected: 14 项测试通过。

Run: `npm.cmd run build`

Expected: Vite 构建成功。

- [ ] **Step 3: 重启后端并验证真实模型**

停止旧后端进程，以正常环境启动 `python -m uvicorn main:app --host 127.0.0.1 --port 8000`。提交一条最小开放回答并触发分析，确认接口返回下一问且服务日志没有鉴权或模型不存在错误。

- [ ] **Step 4: 确认前端仍可访问**

请求 `http://127.0.0.1:5173/`，确认状态码为 200；保留前后端服务运行供用户检查。
