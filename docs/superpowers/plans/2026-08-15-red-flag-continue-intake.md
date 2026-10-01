# 危险信号不中断问诊实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 危险信号改为持续安全提示，患者仍按信息完整度继续完成诊前问诊。

**Architecture:** 后端停止策略不再因 `red_flags` 直接返回结束，而是把危险信号保存在会话安全提醒中并继续选择下一字段。前端在整理、追问和结果阶段统一渲染醒目的持续安全提醒。

**Tech Stack:** Python 3.14、FastAPI、Vue 3、Python `unittest`、Node `node:test`

## Global Constraints

- 危险信号不得从患者记录、医生摘要或最终档案中删除。
- 危险信号不得触发新会话自动暂停或自动完成。
- 信息完整度、字段级两次上限和去重规则保持不变。
- 存在危险信号时不推荐普通检查套餐。
- 不输出诊断、处方或治疗建议。
- 当前目录没有 Git 元数据，不初始化 Git，不伪造提交。

---

### Task 1: 修改危险信号停止策略

**Files:**
- Modify: `backend/tests/test_intake_question_policy.py`
- Modify: `backend/tests/test_intake_flow.py`
- Modify: `backend/intake_question_policy.py`

**Interfaces:**
- Consumes: `decide_stop(..., red_flags: list[str], ...) -> dict`
- Produces: 危险信号存在时仍返回 `continue_collecting` 或正常完整度停止结果

- [ ] **Step 1: 写危险信号继续追问失败测试**

构造空字段状态和 `red_flags=["胸痛"]`，断言 `decide_stop()` 返回 `stop=False`、`reason="continue_collecting"`，下一字段仍由优先级选择。

- [ ] **Step 2: 运行测试确认旧逻辑失败**

Run: `python -m unittest tests.test_intake_question_policy -v`

Expected: 旧代码返回 `red_flag_escalation`，新测试失败。

- [ ] **Step 3: 删除危险信号直接停止分支**

从 `decide_stop()` 删除 `if red_flags: return _stop("red_flag_escalation")`，保留参数兼容、执行度和字段选择逻辑。

- [ ] **Step 4: 验证会话持续保存安全提醒**

增加会话测试：应用包含 `red_flags=["胸痛"]` 且决策继续的分析结果后，阶段为 `follow_up`，`safety_alerts` 包含“胸痛”。

- [ ] **Step 5: 运行后端定向测试**

Run: `python -m unittest tests.test_intake_question_policy tests.test_intake_flow tests.test_intake_views -v`

Expected: 危险信号继续追问并持续保存测试全部通过。

### Task 2: 增加前端持续安全提醒

**Files:**
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Consumes: `state.safety_alerts: string[]`
- Produces: 整理、追问、结果阶段一致的安全提醒

- [ ] **Step 1: 写三阶段安全提示失败测试**

提取 `analyzing`、`follow_up_chat` 和 `result` 模板区块，断言都使用 `state.safety_alerts`；断言结果页危险信号存在时显示“优先线下评估，暂不提供常规检查建议”。

- [ ] **Step 2: 运行前端测试确认失败**

Run: `npm.cmd test`

Expected: 整理阶段和正常结果阶段缺少安全提示，新增测试失败。

- [ ] **Step 3: 实现统一提示内容**

在三个阶段的标题下方渲染红色提醒，包含识别项列表和“仍可继续填写；症状正在发生或加重时及时就医”的说明。将追问阶段原提示移动到标题下方，避免重复。

- [ ] **Step 4: 调整结果页空检查文案**

当 `state.safety_alerts.length > 0` 且没有检查建议时显示优先线下评估文案；无危险信号时保留普通空状态。

- [ ] **Step 5: 运行前端测试**

Run: `npm.cmd test`

Expected: 全部前端测试通过。

### Task 3: 全量验证与服务恢复

**Files:**
- Test: `backend/tests/*.py`
- Test: `frontend/tests/*.test.mjs`

**Interfaces:**
- Consumes: 修改后的前后端
- Produces: 可继续试用的 DeepSeek 服务

- [ ] **Step 1: 运行后端全量测试**

Run: `python -m unittest discover -s tests -v`

Expected: 全部测试通过。

- [ ] **Step 2: 运行前端测试和构建**

Run: `npm.cmd test`

Expected: 全部测试通过。

Run: `npm.cmd run build`

Expected: Vite 构建成功。

- [ ] **Step 3: 重启后端并进行浏览器验收**

正常启动 DeepSeek 后端。回答“胸痛”后确认页面继续出现下一问、红色提示持续显示、左侧仍处于补充问诊且不生成完整档案。
