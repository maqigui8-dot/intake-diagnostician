# 成人单纯性肥胖诊前问诊执行度 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox checkpoints and require tests before implementation.

**Goal:** 将现有“固定 10 题 + AI 自行判断是否问够”的通用问诊，改造成面向 18 岁及以上成人单纯性肥胖的开放式诊前问诊；由规则程序计算辨证资料执行度和开方安全执行度，达到明确门槛后停止追问，并为医生提供可追溯的执行度、证据、缺口和停止原因。

**Architecture:** 保留 FastAPI、Vue 3、千问兼容接口和现有档案保存能力。新增肥胖字段库、字段状态合并器、确定性计分器和停止策略器；AI 只做自然语言证据提取和问题表达。患者接口只返回当前自然问题、问答历史、安全提示和最终档案；医生接口单独返回执行度、字段证据和审计信息。

**Tech Stack:** Python 3.14、FastAPI、Pydantic 2、LangChain/OpenAI-compatible Qwen、Vue 3、Vite 6、Python `unittest`、Node `node:test`。

**Global Constraints:**

- 第一版仅支持 18 岁及以上成人单纯性肥胖诊前采集。
- 不输出证型概率、自动诊断、处方、药物剂量或针灸方案。
- `85` 分是工程试行阈值，不能描述为国标诊断阈值。
- 患者端不得返回或渲染执行度、缺失必问项、建议选问项和内部字段状态。
- 危险信号优先于分数；患者无法回答时只允许委婉重问一次。
- 动态追问一般以 4 至 8 轮为目标，12 轮为硬性保护上限，不把固定轮数当作正常完成依据。
- 当前目录没有 Git 元数据。每个任务末尾使用“测试检查点”记录改动文件和测试结果，不初始化 Git、不伪造提交。

## 文件结构

### 新增文件

- `backend/obesity_intake_schema.py`：成人肥胖字段定义、权重、优先级、适用条件、默认问法和规则版本。
- `backend/intake_execution.py`：字段状态合并、执行度计算、门槛判断和医生摘要。
- `backend/intake_question_policy.py`：危险信号优先、字段选择、重问次数和非正常停止原因。
- `backend/intake_views.py`：患者安全响应与医生响应的字段隔离。
- `backend/tests/test_obesity_intake_schema.py`：字段总分、硬必问项和条件字段测试。
- `backend/tests/test_intake_execution.py`：计分、归一化、阈值和审计测试。
- `backend/tests/test_intake_question_policy.py`：追问优先级、重问、去重和停止测试。
- `backend/tests/test_intake_views.py`：患者响应不泄漏内部字段、医生响应完整测试。
- `frontend/src/doctor-view.js`：医生模式识别和执行度展示格式化。
- `frontend/src/components/DoctorExecutionPanel.vue`：医生端执行度、证据和待确认项组件。
- `frontend/tests/doctor-view.test.mjs`：医生模式和展示数据测试。

### 修改文件

- `backend/intake_flow.py`：会话从固定 10 题改为开放回答、动态追问、字段状态和停止结果。
- `backend/skill_analysis.py`：把单次“完整度结论”改为字段证据提取与自然问题生成。
- `backend/follow_up_policy.py`：保留兼容入口，内部委托给新的确定性策略。
- `backend/main.py`：增加开放回答、处理下一轮和医生摘要接口；患者接口使用安全响应。
- `backend/agent.py`：继续加载两个 Skill，支持提取任务和问句生成任务。
- `backend/skills/tcm-intake-checklist/SKILL.md`：限定成人单纯性肥胖，明确两部分执行度和字段依据。
- `backend/skills/tcm-questioning-guide/SKILL.md`：明确开放式首问、单问点和一次委婉重问。
- `backend/tests/test_intake_flow.py`、`backend/tests/test_skill_analysis.py`、`backend/tests/test_follow_up_policy.py`：迁移旧流程测试。
- `frontend/src/App.vue`：固定选项页改为开放式首问、统一聊天追问和患者结果页；医生模式挂载医生组件。
- `frontend/src/follow-up-stage.js`：按会话 `phase` 和 `stop_reason` 切换页面，不再用 `is_complete + AI completeness_status` 推断。
- `frontend/src/style.css`：开放首问、对话区、医生执行度面板和响应式布局。
- `frontend/tests/follow-up-stage.test.mjs`、`frontend/tests/patient-visibility.test.mjs`：更新流程与可见性断言。
- `frontend/build-app.mjs`：使用脚本真实目录作为 Vite 根目录，解决 junction 路径构建失败。

## Task 1: 建立成人肥胖字段库

**Interfaces:**

- `FieldDefinition`：`key`、`section`、`group`、`weight`、`priority`、`hard_required`、`conditional`、`max_attempts`、`question`、`retry_question`、`source`。
- `FIELD_DEFINITIONS: Sequence[FieldDefinition]`
- `get_field_definition(key: str) -> FieldDefinition`
- `get_applicable_fields(context: dict[str, object]) -> Sequence[FieldDefinition]`

**Files:**

- Create: `backend/obesity_intake_schema.py`
- Create: `backend/tests/test_obesity_intake_schema.py`

- [ ] **Step 1: 先写失败测试，锁定 70/30 分配和硬必问项**

```python
def test_registry_weights_are_70_and_30(self):
    differentiation = sum(item.weight for item in FIELD_DEFINITIONS if item.section == "differentiation")
    safety = sum(item.weight for item in FIELD_DEFINITIONS if item.section == "safety")
    self.assertEqual(differentiation, 70)
    self.assertEqual(safety, 30)

def test_prescription_safety_hard_required_fields_are_fixed(self):
    hard_keys = {item.key for item in FIELD_DEFINITIONS if item.hard_required}
    self.assertEqual(hard_keys, {"allergies", "medications", "important_history", "red_flags"})
```

- [ ] **Step 2: 运行测试并确认因模块不存在而失败**

Run: `python -m unittest tests.test_obesity_intake_schema -v`

Expected: `ModuleNotFoundError: No module named 'obesity_intake_schema'`

- [ ] **Step 3: 实现不可变字段定义和明确权重**

```python
@dataclass(frozen=True)
class FieldDefinition:
    key: str
    section: Literal["differentiation", "safety"]
    group: str
    weight: int
    priority: int
    hard_required: bool
    conditional: str | None
    max_attempts: int
    question: str
    retry_question: str
    source: str
```

字段权重必须按设计文档落地：辨证资料为 `4+5+2+4+4+3+3+6+5+5+5+5+5+4+5+2+1+1+1=70`，开方安全为 `6+6+7+5+3+3=30`。妊娠字段使用 `conditional="pregnancy_applicable"`，舌象为可选字段且不得成为硬阻断项。

- [ ] **Step 4: 增加字段 key 唯一、条件字段适用性和默认问法非空测试**

Run: `python -m unittest tests.test_obesity_intake_schema -v`

Expected: 所有字段库测试通过。

- [ ] **Step 5: 测试检查点**

记录改动：`obesity_intake_schema.py`、`test_obesity_intake_schema.py`；保存测试命令与通过数量。

## Task 2: 实现确定性执行度计分器

**Interfaces:**

- `merge_field_updates(current, updates, source_turn) -> dict[str, dict]`
- `calculate_execution(field_states, context) -> dict`
- `evaluate_threshold(execution, field_states, context) -> dict`
- 状态仅允许 `confirmed`、`partial`、`not_asked`、`unavailable`、`not_applicable`。

**Files:**

- Create: `backend/intake_execution.py`
- Create: `backend/tests/test_intake_execution.py`

- [ ] **Step 1: 写失败测试覆盖系数、条件分母和硬门槛**

```python
def test_confirmed_and_partial_use_fixed_coefficients(self):
    states = blank_states()
    states["main_goal"] = {"status": "confirmed", "evidence": "希望减重", "confidence": 0.96}
    states["height_weight"] = {"status": "partial", "evidence": "体重约 80 公斤", "confidence": 0.75}
    result = calculate_execution(states, {"pregnancy_applicable": False})
    self.assertEqual(result["raw_points"]["main_goal"], 4.0)
    self.assertEqual(result["raw_points"]["height_weight"], 2.5)

def test_score_85_does_not_finish_when_allergy_was_not_asked(self):
    states = states_worth_at_least_85_except("allergies")
    decision = evaluate_threshold(calculate_execution(states, {}), states, {})
    self.assertFalse(decision["can_complete"])
    self.assertIn("allergies", decision["blocking_keys"])
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.test_intake_execution -v`

Expected: 因计分器未实现而失败。

- [ ] **Step 3: 实现状态校验、归一化和门槛判断**

```python
STATUS_COEFFICIENTS = {
    "confirmed": 1.0,
    "partial": 0.5,
    "not_asked": 0.0,
    "unavailable": 0.0,
}

NORMAL_THRESHOLDS = {
    "total": 85.0,
    "differentiation": 55.0,
    "safety": 27.0,
}
```

条件字段为 `not_applicable` 时从原始分子和分母同时移除，再把该 section 归一化回 70 或 30。执行度结果包含 `total_score`、`differentiation_score`、`safety_score`、`raw_points`、`blocking_keys`、`rule_version="adult-obesity-intake-v1"`。

- [ ] **Step 4: 实现证据合并与审计**

同一字段保留最新状态、所有患者原话证据、AI 可信度和 `source_turn`。若新旧明确证据冲突，不覆盖旧值，写入 `conflicts` 并把状态降为 `partial`。

- [ ] **Step 5: 跑单元测试**

Run: `python -m unittest tests.test_intake_execution -v`

Expected: 计分、归一化、冲突和阈值测试全部通过。

- [ ] **Step 6: 测试检查点**

记录改动文件和测试结果，确认代码中没有让 AI 提交最终分数的入口。

## Task 3: 实现下一问选择和停止策略

**Interfaces:**

- `select_next_field(field_states, execution, follow_up_answers, context) -> str | None`
- `decide_stop(field_states, execution, follow_up_answers, context, *, red_flags, ai_available) -> dict`
- 停止原因：`threshold_reached`、`red_flag_escalation`、`patient_unavailable`、`safety_limit`、`duplicate_gap`、`no_collectable_gap`、`ai_unavailable`。

**Files:**

- Create: `backend/intake_question_policy.py`
- Create: `backend/tests/test_intake_question_policy.py`
- Modify: `backend/follow_up_policy.py`
- Modify: `backend/tests/test_follow_up_policy.py`

- [ ] **Step 1: 写失败测试覆盖优先级和一次重问**

```python
def test_red_flag_is_selected_before_higher_weight_symptom_gap(self):
    key = select_next_field(states_with_gaps("red_flags", "appetite_thirst"), empty_execution(), [], {})
    self.assertEqual(key, "red_flags")

def test_unknown_answer_retries_same_field_only_once(self):
    history = [{"question_key": "allergies", "answer_quality": "unavailable"}]
    self.assertEqual(select_next_field(blank_states(), empty_execution(), history, {}), "allergies")
    history.append({"question_key": "allergies", "answer_quality": "unavailable"})
    self.assertNotEqual(select_next_field(blank_states(), empty_execution(), history, {}), "allergies")
```

- [ ] **Step 2: 实现选择顺序**

选择顺序固定为：已发现危险信号立即停止；未询问危险信号；开方安全硬必问项；产生冲突的字段；按 `priority` 和未获得分值排序的辨证字段；一般补充字段。相同优先级按字段库顺序保证结果稳定。

- [ ] **Step 3: 实现停止判断**

```python
if red_flags:
    return stop("red_flag_escalation", complete=False)
if len(follow_up_answers) >= 12:
    return stop("safety_limit", complete=False)
if threshold["can_complete"]:
    return stop("threshold_reached", complete=True)
```

只有患者对所有剩余可收集关键字段均拒绝或无法回答时使用 `patient_unavailable`；字段达到询问上限后不得换 key 或换说法继续问；无可收集缺口时使用 `no_collectable_gap`。

- [ ] **Step 4: 让旧 `apply_follow_up_policy` 变成兼容薄层**

旧测试中“选问项不阻断”和“12 轮停止”继续保留，但 `completeness_status` 不再作为最终权威，最终决定来自 `decide_stop`。

- [ ] **Step 5: 跑策略测试**

Run: `python -m unittest tests.test_intake_question_policy tests.test_follow_up_policy -v`

Expected: 危险信号、硬必问、一次重问、去重、85 分门槛和 12 轮保护测试通过。

## Task 4: 把两个 Skill 改造成肥胖专用协作规则

**Interfaces:**

- `tcm-intake-checklist` 只负责字段证据提取规则，不直接给分。
- `tcm-questioning-guide` 接收一个确定的 `field_key`，只生成一个自然问题。
- `parse_extraction_response(text) -> dict`
- `parse_question_response(text, fallback_question) -> str`

**Files:**

- Modify: `backend/skills/tcm-intake-checklist/SKILL.md`
- Modify: `backend/skills/tcm-questioning-guide/SKILL.md`
- Modify: `backend/skill_analysis.py`
- Modify: `backend/agent.py`
- Modify: `backend/tests/test_skill_analysis.py`

- [ ] **Step 1: 先写解析契约测试**

```python
def test_extractor_returns_field_evidence_without_scores(self):
    result = parse_extraction_response('{"field_updates":[{"field_key":"allergies","status":"confirmed","evidence":"没有药物过敏","confidence":0.98}],"conflicts":[],"red_flags":[]}')
    self.assertEqual(result["field_updates"][0]["field_key"], "allergies")
    self.assertNotIn("total_score", result)
```

- [ ] **Step 2: 重写提取提示词**

输出 JSON 只允许 `field_updates`、`conflicts`、`red_flags`。每个字段更新包含 `field_key`、`status`、`evidence`、`confidence`；未知 key 丢弃，非法状态降为 `partial`，可信度限制在 `0.0` 至 `1.0`。

- [ ] **Step 3: 重写问句生成提示词**

输入必须包含字段定义、患者最近原话、已问历史和 `attempt_number`。第一次使用开放自然问法；第二次先承接“刚才可能不太好判断”，再给更具体的少量选项。生成失败时使用字段库的 `question` 或 `retry_question`，保证流程不会卡死。

- [ ] **Step 4: 更新两个 Skill 内容**

检查 Skill 必须出现：`成人单纯性肥胖`、`辨证资料执行度`、`开方安全执行度`、`AI 不直接计分`。问句 Skill 必须出现：`开放式首问`、`每轮一个信息点`、`只允许委婉重问一次`、`不得向患者展示内部缺口名称或执行度`。

- [ ] **Step 5: 跑分析和 Skill 测试**

Run: `python -m unittest tests.test_skill_analysis -v`

Expected: JSON 解析、非法输出回退、双 Skill 加载、无分数越权和问句回退测试通过。

## Task 5: 重构会话为开放式首问和动态字段状态

**Interfaces:**

- 会话 `phase`：`open_intake`、`processing`、`follow_up`、`completed`、`escalated`。
- `submit_open_answer(session_id, answer) -> dict`
- `submit_follow_up_answer(session_id, question, answer, question_key, attempt_number) -> dict`
- `apply_analysis_turn(session_id, extraction, question, decision, execution) -> dict`
- `get_internal_intake_state(session_id) -> dict`

**Files:**

- Modify: `backend/intake_flow.py`
- Modify: `backend/tests/test_intake_flow.py`

- [ ] **Step 1: 用新会话契约替换固定 10 题测试**

```python
def test_new_session_starts_with_open_question(self):
    state = get_intake_state("session-a")
    self.assertEqual(state["phase"], "open_intake")
    self.assertIn("最想改善", state["open_question"])
    self.assertEqual(state["follow_up_count"], 0)

def test_open_answer_is_preserved_as_patient_evidence(self):
    state = submit_open_answer("session-a", "体重这半年涨了十斤，饭后容易困")
    self.assertEqual(state["open_answer"], "体重这半年涨了十斤，饭后容易困")
    self.assertEqual(state["phase"], "processing")
```

- [ ] **Step 2: 删除固定 `INTAKE_QUESTIONS` 的流程依赖**

不再维护 `current_index`、`option_id` 和固定 10 题进度。为了读取旧保存记录，`generate_report` 继续接受旧 `structured_answers`，但新会话统一使用 `open_answer`、`follow_up_answers` 和 `field_states`。

- [ ] **Step 3: 实现回答质量和尝试次数存储**

每条追问记录保存 `question_key`、`question`、`answer`、`attempt_number`、`answer_quality`、`created_at`。同一 key 最多两条记录；第 2 次仍不可用时字段标记 `unavailable`。

- [ ] **Step 4: 实现编辑后重新计算**

开放回答或任一追问被医生修正时，清除旧的停止结果，重新合并字段状态、计算分数并追加审计记录，不能静默覆盖历史证据。

- [ ] **Step 5: 跑会话测试**

Run: `python -m unittest tests.test_intake_flow -v`

Expected: 开放首问、动态追问、两次重问上限、报告和审计测试全部通过。

## Task 6: 串联“提取 → 计分 → 选字段 → 生成问题”服务

**Interfaces:**

- `process_intake_turn(session_id: str, agent: Any) -> dict`
- 正常继续：返回 `phase="follow_up"`、`next_question`、`question_key`、`attempt_number`。
- 正常完成：返回 `phase="completed"`、`stop_reason="threshold_reached"`。
- 危险升级：返回 `phase="escalated"`、`stop_reason="red_flag_escalation"`。

**Files:**

- Modify: `backend/skill_analysis.py`
- Modify: `backend/intake_flow.py`
- Modify: `backend/main.py`
- Modify: `backend/tests/test_skill_analysis.py`

- [ ] **Step 1: 写端到端服务测试，使用 FakeAgent**

测试一次开放回答同时提取 `main_goal`、`weight_change`、`appetite_thirst` 后，计分器减少对应缺口，并选择最高优先级尚未询问的安全字段。再测试达到门槛时不调用问题生成器。

- [ ] **Step 2: 实现回合编排**

```python
extraction = extract_fields_with_agent(state, agent)
field_states = merge_field_updates(state["field_states"], extraction["field_updates"], state["turn"])
execution = calculate_execution(field_states, state["context"])
decision = decide_stop(field_states, execution, state["follow_up_answers"], state["context"], red_flags=extraction["red_flags"], ai_available=True)
```

未停止时调用 `select_next_field`，再调用问题生成器。停止后才生成与已知风险直接相关的检查建议，并将结果保存到会话，避免每轮都提前推荐检查。

- [ ] **Step 3: 实现 AI 不可用回退**

提取失败时，按字段库默认问法依次完成 `red_flags`、`allergies`、`medications`、`important_history`；固定安全项问完后以 `ai_unavailable` 结束，档案明确标记辨证资料待医生补充。

- [ ] **Step 4: 跑服务和接口测试**

Run: `python -m unittest tests.test_skill_analysis tests.test_intake_flow -v`

Expected: 正常继续、阈值停止、危险信号、AI 回退和检查建议延迟生成全部通过。

## Task 7: 隔离患者响应和医生响应

**Interfaces:**

- `build_patient_state(internal_state) -> dict`
- `build_doctor_summary(internal_state) -> dict`
- `GET /api/intake/session/{session_id}`：患者安全状态。
- `POST /api/intake/session/{session_id}/open-answer`
- `POST /api/intake/session/{session_id}/follow-up`
- `GET /api/intake/session/{session_id}/doctor-summary`：原型医生视图数据。

**Files:**

- Create: `backend/intake_views.py`
- Create: `backend/tests/test_intake_views.py`
- Modify: `backend/main.py`
- Modify: `backend/tests/test_skill_analysis.py`

- [ ] **Step 1: 写患者数据泄漏失败测试**

```python
def test_patient_state_excludes_internal_execution_fields(self):
    public = build_patient_state(sample_internal_state())
    self.assertNotIn("execution", public)
    self.assertNotIn("field_states", public)
    self.assertNotIn("blocking_keys", json.dumps(public, ensure_ascii=False))
```

- [ ] **Step 2: 实现白名单患者响应**

患者响应只允许 `session_id`、`phase`、`open_question`、`open_answer`、`follow_up_answers`、`next_question`、`question_key`、`attempt_number`、`safety_alerts`、`report_markdown`、`recommended_exams`、`stop_reason_public`。不要使用删除黑名单字段的方式。

- [ ] **Step 3: 实现医生摘要**

医生摘要包含总分、两部分分数、是否满足正常门槛、停止原因、规则版本、四种字段状态分组、开方安全字段、患者原话证据、冲突、完整问答和审计记录。

- [ ] **Step 4: 标注原型权限边界**

当前项目没有身份认证，医生接口属于本地演示的数据视图隔离，不宣称具备生产级权限控制。接口返回增加 `access_scope="prototype_doctor_view"`，部署前必须接入真实医生身份认证。

- [ ] **Step 5: 跑视图和接口测试**

Run: `python -m unittest tests.test_intake_views tests.test_skill_analysis -v`

Expected: 患者无内部字段泄漏，医生摘要字段齐全，接口状态码和请求模型正确。

## Task 8: 改造患者端为开放首问和统一聊天流程

**Interfaces:**

- `getIntakeViewStage({ state, loading, saving })`
- 页面阶段：`open_intake`、`analyzing`、`follow_up_chat`、`result`、`escalated`。

**Files:**

- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/follow-up-stage.js`
- Modify: `frontend/src/style.css`
- Modify: `frontend/tests/follow-up-stage.test.mjs`
- Modify: `frontend/tests/patient-visibility.test.mjs`

- [ ] **Step 1: 先更新流程测试**

```javascript
test('开放回答后进入整理阶段', () => {
  assert.equal(getIntakeViewStage({ state: { phase: 'processing' } }), 'analyzing')
})

test('危险信号结束时显示线下就医提示', () => {
  assert.equal(getIntakeViewStage({ state: { phase: 'escalated' } }), 'escalated')
})
```

- [ ] **Step 2: 将固定选项页替换为开放式首问**

首屏显示设计文档中的开放问题和一个大文本框；发送后直接进入现有对话区域。删除患者端“问题 1/10”、固定选项、上一题、下一题和右侧固定进度，保留左侧流程说明但不显示内部缺失项。

- [ ] **Step 3: 统一所有后续问答为聊天气泡**

页面只使用后端返回的 `next_question` 和 `attempt_number`。第 2 次询问不显示“重问失败”等内部标签，只呈现更友好的自然问句。不得在前端自行判断 85 分或选择问题。

- [ ] **Step 4: 增加异常结束界面**

`red_flag_escalation` 显示明确线下就医提示；`safety_limit`、`patient_unavailable`、`no_collectable_gap`、`ai_unavailable` 使用面向患者的中性说明，并允许保存已收集档案。

- [ ] **Step 5: 跑前端测试**

Run: `npm.cmd test`

Expected: 新流程测试通过，患者模板仍不包含“信息完整度”“缺失必问项”“建议选问项”“辨证资料执行度”“开方安全执行度”。

## Task 9: 增加医生端执行度与证据视图

**Interfaces:**

- `isDoctorView(search: string) -> boolean`
- `formatStopReason(reason: string) -> string`
- `DoctorExecutionPanel` props：`summary`、`loading`、`error`。

**Files:**

- Create: `frontend/src/doctor-view.js`
- Create: `frontend/src/components/DoctorExecutionPanel.vue`
- Create: `frontend/tests/doctor-view.test.mjs`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

- [ ] **Step 1: 写医生模式和停止原因格式化测试**

```javascript
test('只有明确 doctor 参数才进入医生视图', () => {
  assert.equal(isDoctorView('?view=doctor'), true)
  assert.equal(isDoctorView(''), false)
})

test('阈值完成显示可理解中文', () => {
  assert.equal(formatStopReason('threshold_reached'), '已达到正常完成门槛')
})
```

- [ ] **Step 2: 实现医生面板**

顶部显示总执行度、辨证资料执行度、开方安全执行度和停止原因；中部按“已明确、部分明确、患者无法提供、待诊中确认”分组；底部突出过敏、用药、重要病史和危险信号，并可展开查看患者原话证据和问答历史。

- [ ] **Step 3: 保持患者默认视图不加载医生接口**

只有 `?view=doctor` 时请求 `/doctor-summary` 并挂载组件。默认患者模式既不渲染医生组件，也不请求医生数据。

- [ ] **Step 4: 跑医生视图和患者可见性测试**

Run: `npm.cmd test`

Expected: 医生格式化和组件结构测试通过，患者默认模板检查继续通过。

## Task 10: 更新诊前档案、保存记录和检查建议

**Interfaces:**

- `generate_report(open_answer, follow_up_answers, field_states) -> str`
- `SaveRecordRequest` 新增 `stop_reason`、`rule_version`，医生摘要只由后台从会话生成，不信任前端提交的分数。

**Files:**

- Modify: `backend/intake_flow.py`
- Modify: `backend/main.py`
- Modify: `backend/tests/test_intake_flow.py`
- Modify: `backend/tests/test_skill_analysis.py`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 写失败测试锁定档案内容**

档案必须包含开放主诉、动态问答、已提取的肥胖相关资料、开方安全资料、待诊中确认项、舌脉待采集说明和停止原因；不得包含自动证型、处方或内部 AI 可信度。

- [ ] **Step 2: 由后台保存可信执行度**

保存记录时根据 `session_id` 读取内部会话并写入医生摘要，忽略前端提交的 `total_score`。旧记录缺少新字段时仍能正常读取。

- [ ] **Step 3: 检查建议只在结束阶段出现**

推荐项目与已知肥胖风险和患者资料直接关联，包含名称、方式、科室、意义、优先级和注意事项，不含价格，不把体检套餐全部照搬。

- [ ] **Step 4: 跑后端回归测试**

Run: `python -m unittest discover -s tests -v`

Expected: 新旧记录兼容、档案内容、安全字段和保存防篡改测试全部通过。

## Task 11: 修复 Vite junction 构建并完成全量验证

**Files:**

- Modify: `frontend/build-app.mjs`
- Modify: `frontend/dev-server.mjs`
- Test: all backend and frontend tests

- [ ] **Step 1: 用脚本真实目录固定 Vite root**

```javascript
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('.', import.meta.url))
```

在 `build()` 和 `createServer()` 中使用 `root`，避免从 junction 目录执行时 Rollup 收到 `../../project/intake-diagnostician/frontend/index.html`。

- [ ] **Step 2: 跑后端全量测试**

Run: `python -m unittest discover -s tests -v`

Expected: 全部测试 `OK`，无失败和错误。

- [ ] **Step 3: 跑前端全量测试与生产构建**

Run: `npm.cmd test`

Expected: 全部 Node 测试通过。

Run: `npm.cmd run build`

Expected: 输出包含 `built in`，退出码为 0，`frontend/dist/index.html` 存在。

- [ ] **Step 4: 启动本地服务并做浏览器验收**

Backend: `python -m uvicorn main:app --host 127.0.0.1 --port 8000`

Frontend: `npm.cmd run dev`

患者页验收：开放首问、自然对话、一次友好重问、结果档案和检查建议；全程不出现执行度和内部缺口。

医生页验收：`http://127.0.0.1:5173/?view=doctor` 显示三项分数、停止原因、字段证据和开方安全摘要。

- [ ] **Step 5: 执行 13 个设计验收场景**

逐项覆盖设计文档第 11 节，包括丰富开放回答、四类常见肥胖证候资料覆盖、安全项缺失、两次不知道、重复 key、矛盾回答、危险信号、85 分正常结束、12 轮保护、AI 不可用、条件字段归一化、医生修正审计和无可收集缺口。

- [ ] **Step 6: 最终测试检查点**

记录所有修改文件、测试通过数量、构建结果、浏览器截图位置和仍需中医人员审核的字段权重/阈值。明确 `85` 仍是待校准的工程阈值。

## 自检清单

- [ ] 设计文档第 12 节的每项第一版交付范围都有对应任务。
- [ ] 所有新增接口、函数和字段均有明确名称，没有待办标记或省略占位符。
- [ ] 患者响应使用白名单，执行度和内部缺口不会通过网络响应泄漏。
- [ ] 规则程序是最终计分与停止权威，AI 输出不能直接覆盖分数。
- [ ] 危险信号、一次重问、12 轮上限和 AI 回退都有自动化测试。
- [ ] 医生端显示证据和停止原因，但不显示自动证型结论或处方。
- [ ] 前后端测试及 Vite 构建均能从当前 junction 工作目录运行。
