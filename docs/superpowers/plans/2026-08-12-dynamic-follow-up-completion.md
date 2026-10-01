# 动态追问结束规则 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 取消固定五轮追问限制，让追问是否结束完全由每轮智能完整度分析结果决定。

**Architecture:** 后端只负责持久保存任意数量的追问记录，分析 Agent 每轮根据当前完整资料返回 `complete` 或 `needs_follow_up`。前端只消费这一分析状态，存在当前问题时继续对话，否则进入结果页，不再根据次数截断流程。

**Tech Stack:** Python、FastAPI、unittest、Vue 3、Node.js test runner、Vite。

## Global Constraints

- 页面不得显示固定追问总数、内部完整度、缺失必问项或建议选问项。
- 每轮仍只展示和回答一个追问问题。
- 不修改辨证、诊断、处方等医疗边界。
- 项目不是 Git 仓库，不执行提交、合并或分支操作。

---

### Task 1: 后端取消追问次数拦截

**Files:**
- Modify: `backend/tests/test_intake_flow.py`
- Modify: `backend/intake_flow.py`

**Interfaces:**
- Consumes: `submit_follow_up_answer(session_id: str, question: str, answer: str) -> dict`
- Produces: 可持续追加追问记录且始终返回最新 `follow_up_count` 的问诊状态。

- [ ] **Step 1: 写入失败测试**

将原“达到上限后拒绝”测试改为连续提交六次并断言：

```python
def test_follow_up_answers_are_not_limited_to_five_rounds(self):
    complete_intake_session("session-a")
    for index in range(6):
        state = submit_follow_up_answer("session-a", f"补充问题 {index}", f"回答 {index}")
    self.assertEqual(state["follow_up_count"], 6)
    self.assertNotIn("max_follow_up_answers", state)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest backend.tests.test_intake_flow.IntakeFlowTests.test_follow_up_answers_are_not_limited_to_five_rounds -v`

Expected: 第六次提交抛出“补充问诊已达到上限”。

- [ ] **Step 3: 完成最小后端修改**

删除 `MAX_FOLLOW_UP_ANSWERS`、`get_intake_state()` 返回的 `max_follow_up_answers`，以及 `submit_follow_up_answer()` 中按次数拒绝提交的分支。保留 `follow_up_count` 作为历史轮次统计。

- [ ] **Step 4: 运行后端定向测试**

Run: `python -m unittest backend.tests.test_intake_flow -v`

Expected: 所有问诊流程测试通过。

---

### Task 2: 前端改为仅按分析结果决定阶段

**Files:**
- Modify: `frontend/tests/follow-up-stage.test.mjs`
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/src/follow-up-stage.js`
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Consumes: `skillAnalysis.status`、`skillAnalysis.completeness_status`、`skillAnalysis.follow_up_questions[0]`。
- Produces: `getIntakeViewStage(...)` 不读取追问次数；界面只显示“第 N 问”。

- [ ] **Step 1: 写入失败测试**

新增高轮次仍继续追问测试：

```js
test('追问次数不决定流程结束', () => {
  assert.equal(getIntakeViewStage({
    state: { ...completedState, follow_up_count: 12 },
    skillAnalysis: {
      status: 'completed',
      completeness_status: 'needs_follow_up',
      follow_up_questions: ['仍需确认的问题'],
    },
  }), 'follow_up_chat')
})
```

模板测试增加：不得出现 `max_follow_up_answers`、`followUpLimitReached` 和固定 `/ 5` 展示。

- [ ] **Step 2: 运行前端测试确认失败**

Run: `npm.cmd test`

Expected: 高轮次阶段测试和模板隐藏测试失败。

- [ ] **Step 3: 完成最小前端修改**

从 `getIntakeViewStage()` 删除 `followUpCount < followUpMax` 条件。在 `App.vue` 中把轮次文案改成：

```vue
<span class="chat-round">第 {{ currentFollowUpRound }} 问</span>
```

分析阶段显示“正在整理回答”；删除 `followUpLimitReached`、上限结果提示、提交函数中的上限拦截和按最大值截断轮次的计算。

- [ ] **Step 4: 运行前端测试和构建**

Run: `npm.cmd test`

Expected: 全部前端测试通过。

Run: `npm.cmd run build`

Expected: Vite 构建成功。

---

### Task 3: 分析提示词和 Skill 同步取消五轮规则

**Files:**
- Modify: `backend/tests/test_skill_analysis.py`
- Modify: `backend/skill_analysis.py`
- Modify: `backend/skills/tcm-questioning-guide/SKILL.md`

**Interfaces:**
- Consumes: 当前结构化回答和完整追问历史。
- Produces: Agent 仅根据资料是否够用决定是否返回下一个问题。

- [ ] **Step 1: 写入失败测试**

新增源码规则测试：

```python
def test_analysis_and_questioning_skill_do_not_use_a_fixed_round_limit(self):
    backend_dir = Path(__file__).resolve().parents[1]
    prompt_source = (backend_dir / "skill_analysis.py").read_text(encoding="utf-8")
    skill_source = (backend_dir / "skills" / "tcm-questioning-guide" / "SKILL.md").read_text(encoding="utf-8")
    self.assertNotIn("max_follow_up_answers", prompt_source)
    self.assertNotIn("最多进行 5 轮", skill_source)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest backend.tests.test_skill_analysis.SkillConfigurationTests.test_analysis_and_questioning_skill_do_not_use_a_fixed_round_limit -v`

Expected: 提示词和 Skill 仍含固定上限，测试失败。

- [ ] **Step 3: 修改规则文本**

从分析载荷删除 `max_follow_up_answers`，把提示词改为：只要仍缺影响后续判断的关键信息，就返回一个不重复的自然追问；信息足够时返回空数组。删除 questioning Skill 中“五轮上限”条目。

- [ ] **Step 4: 执行完整验收**

Run: `python -m unittest discover -s backend/tests -q`

Expected: 后端测试全部通过。

Run: `npm.cmd test`

Expected: 前端测试全部通过。

Run: `npm.cmd run build`

Expected: 生产构建成功。

Run: `rg -n "MAX_FOLLOW_UP_ANSWERS|max_follow_up_answers|最多进行 5 轮|第 .* / .* 问|followUpLimitReached" backend frontend/src frontend/tests`

Expected: 无匹配。
