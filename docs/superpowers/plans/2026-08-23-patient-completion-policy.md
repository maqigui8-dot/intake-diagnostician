# Patient Completion Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让患者端在核心资料闭环后结束追问，其余细节转交医生诊中确认。

**Architecture:** 保留现有 `evaluate_threshold` 供医生详细执行度使用；在 `intake_execution.py` 新增 `evaluate_patient_readiness` 作为患者端停止和保存判定。选题策略只从未完成核心字段中取下一问，流程和保存接口统一使用患者完成度。

**Tech Stack:** Python、FastAPI、unittest、Vue 3。

## Global Constraints

- 基础测量、核心病程/症状及用药安全字段不得因缩短追问被跳过。
- 患者端不得展示分数、缺口或字段键。
- 医生端详细执行度算法必须保留。

---

### Task 1: 患者完成度规则

**Files:**
- Modify: `backend/intake_execution.py`
- Modify: `backend/tests/test_intake_execution.py`

- [ ] **Step 1: 写失败测试**

```python
readiness = evaluate_patient_readiness(field_states, context)
assert readiness["can_complete"] is True
assert readiness["blocking_keys"] == []
```

- [ ] **Step 2: 验证失败并实现**

Run: `python -m unittest tests.test_intake_execution -v`
Expected: FAIL，函数尚未定义；实现后 PASS。

### Task 2: 核心优先追问与流程结束

**Files:**
- Modify: `backend/intake_question_policy.py`
- Modify: `backend/intake_flow.py`
- Modify: `backend/main.py`
- Modify: `backend/intake_views.py`
- Modify: `backend/tests/test_intake_question_policy.py`
- Modify: `backend/tests/test_intake_flow.py`

- [ ] **Step 1: 写失败测试**

```python
decision = decide_stop(field_states, execution, history, context)
assert decision["complete"] is True
assert decision["reason"] == "core_information_ready"
```

- [ ] **Step 2: 验证失败并实现**

Run: `python -m unittest tests.test_intake_question_policy -v`
Expected: FAIL；实现后 PASS。

### Task 3: 全量验证

**Files:**
- Modify: `docs/superpowers/plans/2026-08-23-patient-completion-policy.md`

- [ ] **Step 1: 运行测试与构建**

Run: `python -m unittest discover -s tests -v`、`npm.cmd test`、`npm.cmd run build`。

- [ ] **Step 2: 浏览器检查**

确认患者端结果文案不显示内部执行度，且项目可正常打开。
