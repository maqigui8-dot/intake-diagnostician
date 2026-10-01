# Task 7 Brief

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

### Task 7: 医生端分层档案和检查候选

**Controller notes (resolves cross-task scope):**

1. **Exam item shape:** the interface requires every exam to return `name`, `reason`, `trigger`, `priority`, `source`, `rule_version`, `precautions`. Add the missing `trigger`/`source`/`rule_version` fields to `build_recommended_exams`, but KEEP the existing `type` and `department` fields — they are rendered by the patient result view in `frontend/src/App.vue`, which is NOT in this task's file list. Do not modify `App.vue`.
2. **Doctor summary restructure:** `build_doctor_summary` must add `baseline_assessment` (from `internal_state["baseline"]` + `["bmi_assessment"]`) and `layer_execution` (the layer scores already present in `execution`). Reorganize `field_groups` into the design's six sections: 基础测量、病程病因、相关风险、生活心理、中医资料、待医生确认. You may keep or replace the existing status-based `field_groups` / `safety_fields` / `legacy_fields`; whichever you choose, update the existing tests in `backend/tests/test_intake_views.py` to match. Keep `execution`, `blocking_keys`, `conflicts`, `safety_alerts`, `rule_version` available.
3. **Patient/doctor serializers stay separate** — `build_patient_state` (Task 6) must NOT gain execution details here; only `build_doctor_summary` carries them.

**Exam-candidate triggering rules (for `build_recommended_exams`):** abnormal/risk field evidence triggers relevant candidates; missing data alone must not produce a diagnosis; every item carries `source` and `rule_version`; red flags suppress the routine package while the safety alert remains a separate field.

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
