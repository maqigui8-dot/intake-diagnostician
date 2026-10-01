# 对话式追问 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将基础问诊后的补问改为独立聊天阶段，并隐藏患者不需要看到的完整度、缺失项和选问项。

**Architecture:** 从现有 `App.vue` 中抽取一个纯函数，根据问诊会话、分析状态和追问上限推导 `base_intake`、`analyzing`、`follow_up_chat`、`result`、`analysis_unavailable` 五个页面阶段。Vue 仅按阶段渲染，后台分析 JSON 和保存协议保持不变；聊天记录继续以 `follow_up_answers` 为唯一来源。

**Tech Stack:** Vue 3、Vite、原生 Fetch API、Node.js 内置测试运行器、Python unittest。

## Global Constraints

- 患者界面不得展示“信息完整度”“缺失必问项”“建议选问项”。
- 安全提示必须保留并在需要时立即显示。
- 每轮只展示一个待回答问题，最多补问 5 轮。
- 追问结束前隐藏最终档案和检查建议。
- 分析失败时保留基础档案和聊天历史，并提供重新分析入口。
- 不改变现有后端接口和记录结构。

---

### Task 1: 页面阶段推导

**Files:**
- Create: `frontend/src/follow-up-stage.js`
- Create: `frontend/tests/follow-up-stage.test.mjs`
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: `{ state, skillAnalysis, analysisLoading, followUpSaving }`。
- Produces: `getIntakeViewStage(context): 'base_intake' | 'analyzing' | 'follow_up_chat' | 'result' | 'analysis_unavailable'`。

- [ ] **Step 1: Write the failing test**

测试覆盖：基础题未完成、正在分析、需要补问、分析完成、达到上限、分析不可用六种状态。

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/follow-up-stage.test.mjs`

Expected: FAIL because `../src/follow-up-stage.js` does not exist。

- [ ] **Step 3: Write minimal implementation**

实现纯函数：未完成基础问诊返回 `base_intake`；加载或提交追问返回 `analyzing`；分析不可用返回 `analysis_unavailable`；仍需补问且存在当前问题且未达上限返回 `follow_up_chat`；其余返回 `result`。

- [ ] **Step 4: Run test to verify it passes**

Run: `npm.cmd test`

Expected: all stage tests PASS。

### Task 2: 独立聊天界面

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Create: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Consumes: `getIntakeViewStage()`、`state.follow_up_answers`、`currentFollowUpQuestion`。
- Produces: 独立聊天页面及最终结果页面。

- [ ] **Step 1: Write the failing visibility test**

读取 `App.vue` 模板并断言患者界面不包含三个内部标题，同时应包含对话页标题和消息区标识。

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/patient-visibility.test.mjs`

Expected: FAIL because current template still renders internal fields and lacks chat stage。

- [ ] **Step 3: Implement stage-based rendering**

将现有完成页拆为：

- `analyzing`：小郎中正在整理下一问。
- `follow_up_chat`：历史问答气泡、当前助手气泡、底部输入框与发送按钮。
- `result`：最终档案、安全提示和推荐检查项目。
- `analysis_unavailable`：保留档案、提示失败并提供重试。

移除患者界面中的完整度摘要、缺失必问项和建议选问项。

- [ ] **Step 4: Add interaction details**

使用 `ref` 和 `nextTick` 在新消息出现后滚动到底部；支持 `Ctrl+Enter` 发送；发送期间禁用输入和按钮。

- [ ] **Step 5: Add responsive CSS**

桌面端聊天区稳定高度，输入区固定在对话面板底部；移动端使用单列布局，消息气泡最大宽度 88%，所有文字可换行。

- [ ] **Step 6: Run frontend tests and build**

Run: `npm.cmd test`

Expected: all tests PASS。

Run: `npm.cmd run build`

Expected: Vite production build succeeds without errors。

### Task 3: 回归验证与浏览器验收

**Files:**
- Verify: `backend/tests/test_intake_flow.py`
- Verify: `backend/tests/test_skill_analysis.py`
- Verify: `frontend/src/App.vue`

**Interfaces:**
- Consumes: existing `/complete`、`/analyze`、`/follow-up` endpoints。
- Produces: 可连续补问并最终进入结果页的用户流程。

- [ ] **Step 1: Run backend regression tests**

Run: `python -m unittest discover -s backend/tests -v`

Expected: all existing backend tests PASS。

- [ ] **Step 2: Restart local frontend if needed**

Run: `npm.cmd run dev` from `frontend/` and keep backend on port 8000。

Expected: frontend responds at `http://127.0.0.1:5173/`。

- [ ] **Step 3: Verify browser flow**

Complete the ten base questions, verify that the report remains hidden while follow-up is active, answer one follow-up, and verify a new assistant message or final result appears without exposing internal field labels。

- [ ] **Step 4: Verify layout**

Inspect desktop and mobile widths for overlap, overflow, stable input area and readable message bubbles。

- [ ] **Step 5: Final source scan**

Run: `rg -n "信息完整度|缺失必问项|建议选问项" frontend/src/App.vue`

Expected: no matches in patient-facing template copy。

## Plan Self-Review

- Spec coverage: all page stages, hidden fields, safety alerts, five-round limit, retry behavior and responsive checks are assigned to tasks。
- Placeholder scan: no deferred implementation markers。
- Type consistency: `getIntakeViewStage` and the five stage names are consistent across all tasks。
- Repository note: the current project directory has no `.git`; commit steps are intentionally omitted rather than pretending commits can be created。
