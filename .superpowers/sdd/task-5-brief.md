# Task 5 Brief

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
