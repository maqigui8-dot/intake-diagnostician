# Task 1 Brief

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

