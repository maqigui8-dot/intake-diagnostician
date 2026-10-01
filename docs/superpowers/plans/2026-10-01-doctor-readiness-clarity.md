# Doctor Readiness Clarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 医生端清晰展示诊前资料就绪度及停止追问依据。

**Architecture:** 后端复用既有 `evaluate_patient_readiness` 输出解释性汇总，医生 API 直接提供。前端消费字段键和数量，并保留分层覆盖度作为参考。

**Tech Stack:** Python、unittest、Vue 3、Node.js tests、Vite。

## Global Constraints

- 停止规则不变；只调整医生端解释和展示。
- 非适用字段不计入核心和安全分母。
- 保护性结束不显示为资料已就绪。

---

### Task 1: 后端就绪度摘要

**Files:** `backend/decision_explanation.py`、`backend/intake_views.py`、`backend/tests/test_decision_explanation.py`。

**Interfaces:** `build_decision_explanation(state)` 增加 `readiness`；`build_doctor_summary(state)` 增加 `readiness_summary`。

- [x] 先在 `test_decision_explanation.py` 加入核心齐全但扩展缺失、核心冲突、妊娠不适用及保护性结束用例。
- [x] 执行 `python -m unittest tests.test_decision_explanation -v`，确认新断言失败。
- [x] 在后端摘要中复用 `evaluate_patient_readiness`，计算 `core`、`safety`、`core_conflicts`、`optional_keys`、`blocking_keys`、`status`。
- [x] 重跑定向测试，确认通过。

### Task 2: 医生端清晰展示

**Files:** `frontend/src/components/DecisionExplanationPanel.vue`、`frontend/src/components/DoctorExecutionPanel.vue`、`frontend/src/doctor-decision-summary.js`、`frontend/src/style.css`、`frontend/tests/doctor-decision-summary.test.mjs`、`frontend/tests/doctor-view.test.mjs`。

**Interfaces:** 前端从 `summary.readiness_summary` 获取数字和字段键，`buildDoctorDecisionSummary(fieldGroups, optionalKeys)` 只做文字整理。

- [x] 先更新前端测试，要求选填项来自后端字段键，医生端显示“诊前资料就绪度”“分层资料覆盖度”。
- [x] 执行 `npm test`，确认新断言失败。
- [x] 修改组件文案、布局和摘要辅助函数。
- [x] 执行 `npm test` 和 `npm run build`，确认通过。

### Task 3: 全量核验

**Files:** 上述文件。

- [x] 执行 `python -m unittest discover -s tests -q` 并检查失败数。
- [x] 执行 `npm test`、`npm run build` 并检查退出码。
- [x] 核对设计中的五种状态，报告结果和剩余限制。
