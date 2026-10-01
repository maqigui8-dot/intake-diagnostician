# Task 3 Brief

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

