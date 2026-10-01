# 按信息完整度结束与聊天历史保留实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除全局 12 轮追问上限，并让固定高度聊天框在整理和追问阶段始终保留完整历史。

**Architecture:** 后端继续由确定性执行度、字段状态和字段级最多两次规则决定停止，不再以问答总数截断。前端继续使用后端 `follow_up_answers` 作为唯一历史数据源，两个聊天阶段渲染一致的开放首答和完整问答列表。

**Tech Stack:** Python 3.14、FastAPI、Python `unittest`、Vue 3、Node `node:test`

## Global Constraints

- 不设置任何全局追问轮数上限。
- 每个字段最多询问两次，已确认或耗尽字段不得再次询问。
- 正常完成只由 85/55/27 试行执行度门槛和硬必问项决定。
- 患者端不显示内部执行度、缺失必问项或建议选问项。
- 聊天框保持固定高度和纵向滚动，历史问答不得删除。
- 当前目录没有 Git 元数据，不初始化 Git，不伪造提交。

---

### Task 1: 删除后端全局轮次限制

**Files:**
- Modify: `backend/tests/test_intake_question_policy.py`
- Modify: `backend/tests/test_follow_up_policy.py`
- Modify: `backend/tests/test_intake_flow.py`
- Modify: `backend/intake_question_policy.py`
- Modify: `backend/follow_up_policy.py`
- Modify: `backend/intake_flow.py`
- Modify: `backend/intake_views.py`

**Interfaces:**
- Consumes: `decide_stop(...) -> dict`、`select_next_field(...) -> str | None`
- Produces: 仅由完整度、危险信号、AI 状态和可收集字段决定的停止结果

- [ ] **Step 1: 写超过 12 轮仍继续的失败测试**

构造包含 12 条其他字段历史、仍有一个未询问可收集字段的状态，断言 `decide_stop()` 返回 `stop=False`，并断言兼容策略不会返回 `safety_limit`。

- [ ] **Step 2: 写提交第 13 条回答的失败测试**

构造已有 12 条不同字段回答的会话，设置新的当前字段，提交回答后断言历史长度为 13。

- [ ] **Step 3: 运行定向测试确认因 12 轮限制而失败**

Run: `python -m unittest tests.test_intake_question_policy tests.test_follow_up_policy tests.test_intake_flow -v`

Expected: 新增的继续追问和第 13 条提交测试失败。

- [ ] **Step 4: 删除全局上限实现**

删除 `MAX_FOLLOW_UP_SAFETY_ROUNDS`、`len(follow_up_answers) >= 12`、`follow_up_count >= 12` 和提交回答时的 12 条拦截。保留字段级 `max_attempts` 与无可收集字段结束逻辑。

- [ ] **Step 5: 更新停止原因兼容展示**

新会话不再生成 `safety_limit`。旧记录的 `safety_limit` 可继续转换为中性的“历史问诊已保护性结束”，不得显示 12 轮。

- [ ] **Step 6: 运行后端定向测试**

Run: `python -m unittest tests.test_intake_question_policy tests.test_follow_up_policy tests.test_intake_flow tests.test_intake_views -v`

Expected: 超过 12 条可继续、字段最多两次和无可收集字段停止测试全部通过。

### Task 2: 保留整理阶段和追问阶段完整聊天记录

**Files:**
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/src/App.vue`
- Verify: `frontend/src/style.css`

**Interfaces:**
- Consumes: `state.open_answer`、`state.follow_up_answers`、`state.next_question`
- Produces: 两个聊天阶段一致的可滚动历史列表

- [ ] **Step 1: 写前端模板失败测试**

断言 `analyzing` 和 `follow_up_chat` 两个区块都包含 `ref="messageList"`、开放首答和 `state.follow_up_answers`；断言样式继续包含固定 `max-height` 与 `overflow-y: auto`。

- [ ] **Step 2: 运行前端测试确认失败**

Run: `npm.cmd test`

Expected: 整理阶段缺少开放首答和滚动列表引用，新增测试失败。

- [ ] **Step 3: 统一聊天历史模板行为**

在整理阶段的 `.message-list` 上增加 `ref="messageList"`，补充 `state.open_answer`，继续渲染全部 `follow_up_answers`，末尾显示整理动画。追问阶段保持同样顺序并在末尾显示当前问题。

- [ ] **Step 4: 运行前端测试**

Run: `npm.cmd test`

Expected: 全部前端测试通过。

### Task 3: 全量验证与服务重启

**Files:**
- Test: `backend/tests/*.py`
- Test: `frontend/tests/*.test.mjs`

**Interfaces:**
- Consumes: 完成修改后的前后端
- Produces: 可供用户继续试用的本地服务

- [ ] **Step 1: 运行后端全量测试**

Run: `python -m unittest discover -s tests -v`

Expected: 全部测试通过，且测试名称中不再把 12 轮作为停止规则。

- [ ] **Step 2: 运行前端测试和构建**

Run: `npm.cmd test`

Expected: 全部测试通过。

Run: `npm.cmd run build`

Expected: Vite 构建成功。

- [ ] **Step 3: 重启后端**

停止旧 Uvicorn 进程并正常启动 `python -m uvicorn main:app --host 127.0.0.1 --port 8000`，保留 DeepSeek 配置。

- [ ] **Step 4: 浏览器验收**

完成至少两轮追问，确认聊天框高度不增长、出现纵向滚动、开放首答和全部已问问题仍可向上查看；确认患者页面没有内部执行度。
