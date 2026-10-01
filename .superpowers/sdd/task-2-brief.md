# Task 2 Brief

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

