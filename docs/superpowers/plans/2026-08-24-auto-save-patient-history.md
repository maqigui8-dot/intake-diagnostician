# 问诊档案自动保存实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 问诊达到完整条件后自动保存一次，并让患者历史记录正确显示次数和加载状态。

**Architecture:** 前端监听完成状态并调用现有保存接口；后端按患者和会话标识查重，保证刷新或重试不会重复建档。历史接口异常单独显示，不再冒充“0 次记录”。

**Tech Stack:** Vue 3、Node.js test runner、FastAPI、Python unittest

## Global Constraints

- 不改变现有信息完整度和停止追问规则。
- 同一患者的同一会话最多生成一份历史档案。
- 患者端只展示当前患者自己的历史记录。

---

### Task 1: 自动保存状态判断

**Files:**
- Modify: `frontend/src/follow-up-stage.js`
- Test: `frontend/tests/follow-up-stage.test.mjs`

- [ ] 写出完成、保存中、已保存和未完成状态的测试。
- [ ] 运行测试，确认旧实现失败。
- [ ] 实现 `shouldAutoSaveIntakeRecord`。
- [ ] 运行前端测试。

### Task 2: 患者历史交互

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

- [ ] 完成状态触发一次自动保存。
- [ ] 历史栏显示“共 N 次”。
- [ ] 加载失败显示明确提示，空记录文案说明自动保存。

### Task 3: 后端幂等保存

**Files:**
- Modify: `backend/patient_history.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_patient_history.py`
- Test: `backend/tests/test_skill_analysis.py`

- [ ] 写出按患者和会话查找档案的测试。
- [ ] 运行测试，确认旧实现失败。
- [ ] 保存时写入 `session_id`，已有记录时直接返回原记录。
- [ ] 运行后端测试。

### Task 4: 验证与启动

**Files:**
- Verify: `frontend/`
- Verify: `backend/`

- [ ] 运行前端测试和构建。
- [ ] 运行后端测试。
- [ ] 重启前后端并检查历史接口。
