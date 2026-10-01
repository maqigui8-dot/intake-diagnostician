# 成人肥胖指南驱动的诊前采集 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有成人肥胖诊前问诊升级为指南驱动的三层采集流程，并修复澄清回答污染字段、AI不可用提前结束和回车不能发送的问题。

**Architecture:** 后端以确定性规则维护基础诊断、病因风险、中医诊前和安全资料四类状态；AI只负责自然语言提取和生成问题。基础测量使用结构化接口提交，BMI、中心性肥胖提示、完成条件和检查候选均由后端计算。患者端隐藏内部执行度，医生端展示各层完成情况、证据和待确认项。

**Tech Stack:** Python 3、FastAPI、unittest、Vue 3、Vite、Node test runner。

## Global Constraints

- 系统仅面向18岁及以上成年人；未成年人不得套用成人BMI规则。
- 不直接确诊、不输出患病概率、不自动辨证或开方。
- 患者端只能显示“达到成人肥胖范围，待医生确认”。
- 年龄、生理性别、身高、体重和BMI计算成功是正常完成的硬性条件。
- 安全硬性字段为危险信号、过敏史、当前用药和重要既往疾病。
- 病因与风险资料阈值为80%，中医诊前资料阈值为70%。
- “这是什么”“什么意思”“没听懂”等澄清请求不形成证据、不增加完整度、不消耗追问次数。
- AI不可用时使用固定问题继续采集全部字段。
- 输入框按 Enter 发送，Shift+Enter 换行，中文输入法组合输入期间不得误发送。
- 当前目录不是Git仓库；计划中的每个任务以测试和文件差异检查作为审查点，不执行提交命令。

---

## File Structure

- Create `backend/obesity_diagnosis.py`: 成人BMI、肥胖程度、中心性肥胖和基础测量校验。
- Modify `backend/obesity_intake_schema.py`: 增加字段层级、指南字段和条件字段。
- Modify `backend/intake_execution.py`: 分层计算执行度并实现硬门槛。
- Modify `backend/intake_question_policy.py`: 分层选择下一字段、澄清不计次数、离线继续采集。
- Modify `backend/intake_flow.py`: 保存基础资料、识别澄清回答、生成分层档案。
- Modify `backend/skill_analysis.py`: 阻止澄清回答进入字段提取，限制证据来源。
- Modify `backend/intake_views.py`: 患者端与医生端输出新结构。
- Modify `backend/main.py`: 增加基础资料提交接口。
- Modify `backend/exam_recommendations.py`: 以风险字段触发检查候选并携带依据。
- Modify `backend/skills/tcm-intake-checklist/SKILL.md`: 更新必问、选问和停止规则。
- Modify `backend/skills/tcm-questioning-guide/SKILL.md`: 更新澄清、拒答和解释规则。
- Modify `frontend/src/App.vue`: 基础资料表单、回车发送和新的结果摘要。
- Modify `frontend/src/components/DoctorExecutionPanel.vue`: 医生端分层展示。
- Add/Modify corresponding tests under `backend/tests/` and `frontend/tests/`.

### Task 1: 澄清回答与键盘发送

**Files:**
- Modify: `backend/intake_flow.py:95`
- Modify: `backend/intake_question_policy.py:9`
- Modify: `backend/skill_analysis.py:282`
- Modify: `frontend/src/App.vue:51`
- Test: `backend/tests/test_intake_flow.py`
- Test: `backend/tests/test_intake_question_policy.py`
- Test: `backend/tests/test_skill_analysis.py`
- Test: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Produces: `is_clarification_request(answer: str) -> bool`
- Produces: `answer_quality == "clarification"`
- Produces: `handleComposerEnter(event: KeyboardEvent, submit: () => void) -> void`

- [ ] **Step 1: Write failing backend tests**

```python
def test_clarification_does_not_consume_attempt_or_update_field():
    session = intake_sessions.get("clarify")
    session.update({
        "phase": "follow_up",
        "current_question": "您有明确的药物或食物过敏吗？",
        "current_field_key": "allergies",
        "attempt_number": 1,
    })
    state = submit_follow_up_answer("clarify", "这是什么意思？")
    assert state["follow_up_answers"][-1]["answer_quality"] == "clarification"
    assert state["field_states"]["allergies"]["attempts"] == 0
```

```python
def test_clarification_model_output_cannot_confirm_fields():
    # FakeAgent错误地返回“这是什么”作为多个字段证据。
    state = process_intake_turn("clarify", ClarificationAgent())
    assert state["field_states"]["allergies"]["status"] == "not_asked"
    assert state["field_states"]["main_goal"]["status"] == "not_asked"
    assert state["current_field_key"] == "allergies"
```

- [ ] **Step 2: Run tests and verify the current implementation fails**

Run: `python -m unittest backend.tests.test_intake_flow backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v`

Expected: FAIL because clarification is currently classified as `provided`, consumes an attempt, and AI updates are accepted.

- [ ] **Step 3: Implement clarification classification and filtering**

```python
CLARIFICATION_PATTERNS = (
    "这是什么", "什么意思", "没听懂", "没明白", "能解释", "请解释",
)

def is_clarification_request(answer: str) -> bool:
    compact = "".join(str(answer or "").split()).rstrip("？?!！。")
    return len(compact) <= 24 and any(item in compact for item in CLARIFICATION_PATTERNS)
```

In `submit_follow_up_answer`, record `answer_quality="clarification"`, preserve the history row, keep field attempts unchanged, and reset the turn for analysis. In `process_intake_turn`, discard all model field updates when the latest answer quality is `clarification`; keep the current field eligible and generate an explanatory retry.

- [ ] **Step 4: Write failing frontend source tests**

```javascript
test('回车发送且Shift回车换行', () => {
  assert.match(template, /@keydown\.enter="handleOpenEnter"/)
  assert.match(template, /@keydown\.enter="handleFollowUpEnter"/)
  assert.match(appSource, /event\.isComposing/)
  assert.match(appSource, /event\.shiftKey/)
})
```

- [ ] **Step 5: Implement keyboard handlers**

```javascript
function handleComposerEnter(event, submit) {
  if (event.isComposing || event.shiftKey) return
  event.preventDefault()
  submit()
}

function handleOpenEnter(event) {
  handleComposerEnter(event, submitOpenAnswer)
}

function handleFollowUpEnter(event) {
  handleComposerEnter(event, submitFollowUp)
}
```

Replace both `@keydown.ctrl.enter.prevent` bindings with the dedicated Enter handlers. Update the visible shortcut copy to “按 Enter 发送，Shift + Enter 换行”.

- [ ] **Step 6: Run focused tests**

Run: `python -m unittest backend.tests.test_intake_flow backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v`

Run: `npm test -- --test-name-pattern="回车|对话"`

Expected: all focused tests PASS.

### Task 2: 基础测量和成人肥胖规则

**Files:**
- Create: `backend/obesity_diagnosis.py`
- Create: `backend/tests/test_obesity_diagnosis.py`
- Modify: `backend/intake_flow.py:16`
- Modify: `backend/main.py:90`
- Modify: `backend/tests/test_intake_flow.py`

**Interfaces:**
- Produces: `validate_baseline(payload: dict[str, object]) -> dict[str, object]`
- Produces: `calculate_bmi(height_cm: float, weight_kg: float) -> float`
- Produces: `classify_adult_bmi(bmi: float) -> str`
- Produces: `evaluate_central_obesity(sex: str, waist_cm: float | None, hip_cm: float | None) -> dict[str, object]`
- Produces API: `POST /api/intake/session/{session_id}/baseline`

- [ ] **Step 1: Write failing diagnosis-rule tests**

```python
def test_adult_bmi_and_grade():
    assert calculate_bmi(170, 81) == 28.0
    assert classify_adult_bmi(27.9) == "超重"
    assert classify_adult_bmi(28.0) == "轻度肥胖范围"
    assert classify_adult_bmi(32.5) == "中度肥胖范围"
    assert classify_adult_bmi(37.5) == "重度肥胖范围"
    assert classify_adult_bmi(50.0) == "极重度肥胖范围"

def test_central_obesity_uses_sex_specific_waist_threshold():
    assert evaluate_central_obesity("male", 90, None)["waist_reached"] is True
    assert evaluate_central_obesity("female", 84.9, None)["waist_reached"] is False
    assert evaluate_central_obesity("female", 85, None)["waist_reached"] is True
```

- [ ] **Step 2: Run and verify tests fail because module is missing**

Run: `python -m unittest backend.tests.test_obesity_diagnosis -v`

Expected: FAIL with module import error.

- [ ] **Step 3: Implement deterministic rules**

Use `Decimal` or explicit rounding to one decimal. Reject age below 18, unsupported sex values, height outside 100-250 cm, weight outside 20-500 kg, and non-positive waist/hip values. Return `diagnosis_copy="当前BMI达到成人肥胖范围，最终结果需由医生结合测量和检查确认。"` only when BMI is at least 28.

- [ ] **Step 4: Add baseline state and endpoint**

Add `baseline`, `bmi_assessment`, and `baseline_confirmed` to the session. Define a Pydantic request with `age`, `sex`, `height_cm`, `weight_kg`, optional `waist_cm`, optional `hip_cm`, and `measured_at`. The endpoint validates and stores normalized values before opening conversational intake.

- [ ] **Step 5: Run focused tests**

Run: `python -m unittest backend.tests.test_obesity_diagnosis backend.tests.test_intake_flow -v`

Expected: PASS.

### Task 3: 指南字段注册和分层完整度

**Files:**
- Modify: `backend/obesity_intake_schema.py:10`
- Modify: `backend/intake_execution.py:81`
- Modify: `backend/tests/test_obesity_intake_schema.py`
- Modify: `backend/tests/test_intake_execution.py`

**Interfaces:**
- Extends `FieldDefinition` with `layer: Literal["baseline", "risk", "tcm", "safety"]`
- Produces execution keys: `baseline_ready`, `risk_score`, `tcm_score`, `safety_score`, `total_score`, `blocking_keys`

- [ ] **Step 1: Write failing schema tests**

Verify presence of `childhood_obesity`, `family_history`, `smoking`, `alcohol`, `work_activity`, `binge_eating`, `glucose_tests`, `lipid_tests`, `uric_acid_test`, `liver_tests`, `kidney_tests`, and `thyroid_tests`. Verify each field has a layer and source.

- [ ] **Step 2: Write failing threshold tests**

```python
def test_high_optional_score_cannot_bypass_missing_baseline():
    execution = calculate_execution(confirmed_non_baseline_states(), {})
    result = evaluate_threshold(execution, confirmed_non_baseline_states(), {})
    assert result["can_complete"] is False
    assert "baseline" in result["blocking_keys"]
```

```python
def test_all_layers_must_reach_their_thresholds():
    assert evaluate_threshold(execution, states, context)["can_complete"] == (
        execution["baseline_ready"]
        and execution["risk_score"] >= 80
        and execution["tcm_score"] >= 70
        and execution["safety_score"] >= 100
    )
```

- [ ] **Step 3: Implement field layers and guideline fields**

Keep existing keys where their meaning is unchanged. Split `metabolic_tests` into six structured test groups. Keep pregnancy conditional on applicable sex/context. Mark tongue as optional and keep pulse out of online fields.

- [ ] **Step 4: Implement layer-specific normalized scores**

Calculate each layer independently from applicable field weights. The baseline result comes from session baseline validation, not AI field evidence. Return explicit blockers rather than a single opaque total threshold.

- [ ] **Step 5: Run schema and execution tests**

Run: `python -m unittest backend.tests.test_obesity_intake_schema backend.tests.test_intake_execution -v`

Expected: PASS.

### Task 4: 分层追问、离线回退和停止策略

**Files:**
- Modify: `backend/intake_question_policy.py:17`
- Modify: `backend/skill_analysis.py:282`
- Modify: `backend/tests/test_intake_question_policy.py`
- Modify: `backend/tests/test_skill_analysis.py`

**Interfaces:**
- `select_next_field(...) -> str | None` selects safety, risk, then TCM gaps according to hard requirements and layer thresholds.
- `decide_stop(...) -> dict[str, Any]` completes only when all hard gates pass.

- [ ] **Step 1: Write failing selection tests**

Test baseline blocker, hard safety ordering, risk-before-TCM ordering, clarification retry, contradiction retry, and no fixed round limit.

- [ ] **Step 2: Write failing offline test**

```python
def test_ai_unavailable_continues_all_collectable_fields():
    for key in ("red_flags", "allergies", "medications", "important_history"):
        states[key]["status"] = "confirmed"
    decision = decide_stop(states, calculate_execution(states, context), [], context, ai_available=False)
    assert decision["stop"] is False
    assert decision["next_field_key"] is not None
```

- [ ] **Step 3: Remove the safety-only offline filter**

Allow all applicable fields to use `question_for_field()` when AI extraction or question generation is unavailable. Preserve local extraction for simple height, weight and explicit safety statements, but never mark a field confirmed solely because the model returned a field key.

- [ ] **Step 4: Implement evidence validation**

For every model update, require non-empty evidence that occurs in one of the patient answers after whitespace and punctuation normalization. Reject known clarification-only evidence. Preserve valid multi-field answers.

- [ ] **Step 5: Run policy and analysis tests**

Run: `python -m unittest backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v`

Expected: PASS.

### Task 5: 更新两个Skill

**Files:**
- Modify: `backend/skills/tcm-intake-checklist/SKILL.md`
- Modify: `backend/skills/tcm-questioning-guide/SKILL.md`
- Modify: `backend/tests/test_skill_analysis.py`

**Interfaces:**
- Checklist Skill describes field layers and deterministic completion authority.
- Questioning Skill describes clarification, refusal, contradiction and one-question behavior.

- [ ] **Step 1: Write failing source-contract tests**

Assert the checklist contains “基础诊断硬性字段”“病因与风险资料”“中医诊前资料”“AI不得修改停止条件”. Assert the questioning guide contains “澄清请求不作为医学证据”“先解释再重新询问”“不消耗追问次数”.

- [ ] **Step 2: Update checklist Skill**

Document the four layers, required/conditional/optional classification, threshold ownership, adult-only boundary and physician confirmation language.

- [ ] **Step 3: Update questioning Skill**

Document concise explanations for BMI、腰围、过敏、既往疾病、检查项目 and TCM symptom concepts. Require one main information point per turn and forbid exposing internal scores.

- [ ] **Step 4: Run Skill contract tests**

Run: `python -m unittest backend.tests.test_skill_analysis -v`

Expected: PASS.

### Task 6: 患者端基础资料和结果展示

**Files:**
- Modify: `frontend/src/App.vue:37`
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/follow-up-stage.js`
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/tests/follow-up-stage.test.mjs`

**Interfaces:**
- Patient submits baseline before `open_intake`.
- Patient state exposes `baseline`, `bmi_assessment`, and safe public copy only.

- [ ] **Step 1: Write failing frontend tests**

Assert visible inputs for age, sex, height, weight, waist and measured date. Assert no internal scores or “确诊肥胖症” text. Assert the result renders BMI and the doctor-confirmation copy.

- [ ] **Step 2: Implement the baseline form**

Use numeric inputs with explicit units and constraints. Use a segmented control for sex and an optional waist/hip section. Disable submission until required values are valid. Keep the page operational and compact rather than adding a marketing introduction.

- [ ] **Step 3: Add API submission and error handling**

Submit baseline once, preserve values on validation errors, and allow editing before final report. A changed baseline must recalculate BMI server-side.

- [ ] **Step 4: Run frontend tests and build**

Run: `npm test`

Run: `npm run build`

Expected: all tests PASS and Vite build exits 0.

### Task 7: 医生端分层档案和检查候选

**Files:**
- Modify: `backend/intake_views.py:47`
- Modify: `backend/exam_recommendations.py:6`
- Modify: `backend/tests/test_intake_views.py`
- Modify: `backend/tests/test_exam_recommendations.py`
- Modify: `frontend/src/components/DoctorExecutionPanel.vue`
- Modify: `frontend/tests/doctor-view.test.mjs`

**Interfaces:**
- Doctor summary returns `baseline_assessment`, `layer_execution`, `field_groups`, `conflicts`, `safety_alerts`, and `recommended_exams`.
- Every exam item returns `name`, `reason`, `trigger`, `priority`, `source`, `rule_version`, and `precautions`.

- [ ] **Step 1: Write failing doctor-summary tests**

Verify the doctor view contains BMI inputs and result, all four layers, unavailable fields, evidence and conflicts. Verify the patient state omits execution details.

- [ ] **Step 2: Write failing exam-rule tests**

Verify abnormal/risk fields trigger relevant candidates; missing data alone does not create a diagnosis; every exam has a rule source and trigger. Red flags suppress routine package recommendations while preserving the safety alert.

- [ ] **Step 3: Implement backend doctor summary and exam candidates**

Group data into基础测量、病程病因、相关风险、生活心理、中医资料、待医生确认. Keep patient and doctor serializers separate.

- [ ] **Step 4: Implement doctor panel sections**

Use compact full-width sections and tables. Show layer status and rule version; do not expose editable clinical decisions in this iteration.

- [ ] **Step 5: Run focused tests**

Run: `python -m unittest backend.tests.test_intake_views backend.tests.test_exam_recommendations -v`

Run: `npm test -- --test-name-pattern="医生"`

Expected: PASS.

### Task 8: 全量验证和真实流程检查

**Files:**
- Modify as required only when a failing regression demonstrates a defect.

**Interfaces:**
- No new interfaces.

- [ ] **Step 1: Run all backend tests**

Run: `python -m unittest discover -s backend/tests -v`

Expected: all backend tests PASS with zero failures and errors.

- [ ] **Step 2: Run all frontend tests and build**

Run: `npm test`

Run: `npm run build`

Expected: all frontend tests PASS and build exits 0.

- [ ] **Step 3: Restart current frontend and backend services**

Start backend from `backend/` on `127.0.0.1:8000` and frontend from `frontend/` on `127.0.0.1:5173`. Verify both ports belong to processes started from the current project.

- [ ] **Step 4: Perform browser workflow checks**

Verify desktop and mobile flows for: BMI below 28, BMI at 28, sex-specific waist threshold, “这是什么”, explicit refusal, contradictory hypertension history, red flag with continued collection, AI unavailable fallback, final patient report, and doctor view.

- [ ] **Step 5: Confirm acceptance criteria**

Confirm no early completion without baseline, no clarification evidence pollution, Enter behavior works, all history remains scrollable, patient wording avoids diagnosis, and doctor summary contains all internal evidence needed for review.


