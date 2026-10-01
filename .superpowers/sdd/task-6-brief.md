# Task 6 Brief

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

### Task 6: 患者端基础资料和结果展示

**Files:**
- Modify: `frontend/src/App.vue:37`
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/follow-up-stage.js`
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/tests/follow-up-stage.test.mjs`
- Modify: `backend/intake_views.py`（仅 `build_patient_state`，暴露 `baseline` 与 `bmi_assessment`）
- Modify: `backend/tests/test_intake_views.py`（患者状态暴露基础资料且不暴露内部执行度）

**Interfaces:**
- Patient submits baseline before `open_intake`.
- Patient state exposes `baseline`, `bmi_assessment`, and safe public copy only.

**Controller note (resolves cross-task scope):** The plan lists only frontend files for this task, but its interface requires the patient state to expose `baseline` and `bmi_assessment`. That requires a minimal addition to `backend/intake_views.py::build_patient_state`, which is the patient-side serializer (Task 7 owns the doctor-side `build_doctor_summary`). Add exactly: `"baseline"` and `"bmi_assessment"` keys to the returned dict, and keep excluding `context` / `execution` / `field_states` / `blocking_keys` (internal execution details must NOT reach the patient).

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
