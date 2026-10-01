# 患者个人问诊历史 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为当前患者提供仅限本人访问的已完成问诊历史和安全档案回看。

**Architecture:** 保存档案时写入固定演示患者标识；后端通过独立的患者历史映射模块过滤并清洗记录。Vue 患者端读取专用历史接口，在左侧展示列表，并以只读详情页显示选中的档案。

**Tech Stack:** FastAPI、Python unittest、Vue 3、Vite、Node test runner。

## Global Constraints

- 仅使用 `demo-zhang` 作为当前演示患者标识；该演示隔离不等同于真实身份认证。
- 患者端不得展示完整度、缺口、规则版本、置信度、执行度或医生摘要。
- 无 `patient_id` 的既有记录不得出现在患者端历史中。

---

### Task 1: 患者安全历史映射

**Files:**
- Create: `backend/patient_history.py`
- Create: `backend/tests/test_patient_history.py`
- Modify: `backend/main.py`

**Interfaces:**
- Produces: `DEMO_PATIENT_ID`, `belongs_to_patient(record, patient_id)`, `make_history_item(record)`, `make_patient_history_detail(record)`。

- [ ] **Step 1: 写入失败测试**

```python
assert belongs_to_patient(record, DEMO_PATIENT_ID)
assert make_history_item(record)["status"] == "资料已整理"
assert "doctor_summary" not in make_patient_history_detail(record)
```

- [ ] **Step 2: 运行失败测试**

Run: `python -m unittest tests.test_patient_history -v`
Expected: FAIL，提示 `patient_history` 尚不存在。

- [ ] **Step 3: 实现纯映射模块与专用接口**

```python
data["patient_id"] = DEMO_PATIENT_ID
records = [r for r in load_all_records() if belongs_to_patient(r, DEMO_PATIENT_ID)]
```

- [ ] **Step 4: 运行后端测试**

Run: `python -m unittest discover -s tests -v`
Expected: PASS。

### Task 2: 患者端个人记录列表与只读回看

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Modify: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Consumes: `GET /api/patient/records` 与 `GET /api/patient/records/{record_id}`。
- Produces: `loadHistory()`、`openHistory(recordId)`、`historyDetail` 患者安全只读视图。

- [ ] **Step 1: 写入失败测试**

```js
assert.match(template, /我的问诊记录/)
assert.match(appSource, /\/api\/patient\/records/)
assert.match(appSource, /function openHistory/)
```

- [ ] **Step 2: 运行失败测试**

Run: `npm.cmd test`
Expected: FAIL，提示侧栏历史入口尚不存在。

- [ ] **Step 3: 追加侧栏列表与只读详情页**

```vue
<button v-for="record in historyRecords" @click="openHistory(record.record_id)">
  <strong>{{ record.primary_concern }}</strong>
  <small>{{ formatRecordDate(record.created_at) }} · {{ record.status }}</small>
</button>
```

- [ ] **Step 4: 运行前端测试与构建**

Run: `npm.cmd test; npm.cmd run build`
Expected: PASS，且构建成功。

### Task 3: 端到端人工验证

**Files:**
- Modify: `docs/superpowers/plans/2026-08-23-personal-intake-history.md`

- [ ] **Step 1: 通过浏览器验证**

打开患者端，确认左侧仅出现当前患者已保存档案，打开详情后可回看档案与检查事项，且页面没有医生端完整度字段。

- [ ] **Step 2: 记录验证结果**

将三个任务标记完成，并在本文件末尾记录实际测试命令和结果。
