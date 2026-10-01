# 医生端决策解释栏易读性改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将医生端右栏从难解释的扩展百分比，改为“核心是否完成、已覆盖哪些线索、诊中还应补充什么”的中文摘要。

**Architecture:** 新建一个无界面的纯函数模块，负责把后端 `field_groups` 转换为已覆盖线索和诊中补充项；Vue组件只负责展示。停止规则、数据库结构和后端接口均不改变。

**Tech Stack:** Vue 3、JavaScript ES Modules、Node.js `node:test`、Vite。

## Global Constraints

- 不再展示病因与风险、中医诊前的扩展覆盖百分比。
- 保留核心必问 `已完成数 / 总数`。
- 选填项必须明确说明“不影响档案保存”。
- 安全提醒优先于常规检查建议。
- 不展示英文 `field_key`，缺少字段中文名时使用资料类别名称。
- 当前目录不是Git仓库，因此不执行提交步骤；每个任务以测试通过为检查点。

---

### Task 1: 生成医生可读的资料覆盖摘要

**Files:**
- Create: `frontend/src/doctor-decision-summary.js`
- Create: `frontend/tests/doctor-decision-summary.test.mjs`

**Interfaces:**
- Consumes: `field_groups: Record<string, Array<{field_key:string, group:string, status:string, evidence:string[]}>>`
- Produces: `buildDoctorDecisionSummary(fieldGroups): {covered:Array<{title:string, detail:string}>, pending:string[]}`

- [ ] **Step 1: 写失败测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { buildDoctorDecisionSummary } from '../src/doctor-decision-summary.js'

test('把已确认字段汇总为已覆盖线索', () => {
  const result = buildDoctorDecisionSummary({
    '肥胖病程与可能病因': [
      { field_key: 'onset_course', group: '起病经过与相关因素', status: 'confirmed', evidence: ['一年'] },
    ],
    '中医诊前资料': [
      { field_key: 'stool_urine', group: '中医症状资料', status: 'confirmed', evidence: ['无明显变化'] },
    ],
  })
  assert.deepEqual(result.covered, [
    { title: '病程与风险', detail: '起病经过与相关因素' },
    { title: '中医诊前', detail: '中医症状资料' },
  ])
})

test('把未确认选填字段转换成中文诊中补充项并去重', () => {
  const result = buildDoctorDecisionSummary({
    '中医诊前资料': [
      { field_key: 'cold_heat_sweat', group: '中医症状资料', status: 'not_asked', evidence: [] },
      { field_key: 'tongue', group: '舌象', status: 'not_asked', evidence: [] },
    ],
  })
  assert.deepEqual(result.pending, ['寒热与出汗', '舌象'])
})
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd frontend && node --test tests/doctor-decision-summary.test.mjs`

Expected: FAIL，提示无法导入 `doctor-decision-summary.js`。

- [ ] **Step 3: 实现纯函数模块**

```js
const SECTION_LABELS = {
  '肥胖病程与可能病因': '病程与风险',
  '相关疾病风险': '病程与风险',
  '生活方式与心理情况': '生活方式',
  '中医诊前资料': '中医诊前',
  '待医生确认': '用药与安全',
}

const FIELD_LABELS = {
  family_history: '家族史',
  childhood_obesity: '儿童期体重情况',
  cold_heat_sweat: '寒热与出汗',
  edema_heaviness: '浮肿与身体困重',
  chest_abdomen: '胸腹不适',
  tongue: '舌象',
  smoking: '吸烟情况',
  alcohol: '饮酒情况',
  work_activity: '工作与日常活动',
  stress_eating: '情绪性进食',
}

export function buildDoctorDecisionSummary(fieldGroups = {}) {
  const coveredMap = new Map()
  const pending = []
  for (const [section, fields] of Object.entries(fieldGroups || {})) {
    for (const field of fields || []) {
      if (field.status === 'confirmed' && field.evidence?.length) {
        const title = SECTION_LABELS[section] || section
        const groups = coveredMap.get(title) || []
        if (field.group && !groups.includes(field.group)) groups.push(field.group)
        coveredMap.set(title, groups)
      } else if (['not_asked', 'partial', 'unavailable'].includes(field.status)) {
        const label = FIELD_LABELS[field.field_key] || field.group || SECTION_LABELS[section] || section
        if (label && !pending.includes(label)) pending.push(label)
      }
    }
  }
  return {
    covered: [...coveredMap].map(([title, groups]) => ({ title, detail: groups.join('、') })),
    pending,
  }
}
```

- [ ] **Step 4: 运行测试并确认通过**

Run: `cd frontend && node --test tests/doctor-decision-summary.test.mjs`

Expected: 2 tests PASS。

---

### Task 2: 用中文摘要重构右栏

**Files:**
- Modify: `frontend/src/components/DecisionExplanationPanel.vue`
- Modify: `frontend/src/style.css`
- Modify: `frontend/tests/multi-patient-workspace.test.mjs`

**Interfaces:**
- Consumes: Task 1 的 `buildDoctorDecisionSummary(summary.field_groups)`。
- Produces: 右栏三个主要区块：核心诊前资料、已覆盖主要线索、诊中建议补充。

- [ ] **Step 1: 更新组件契约测试并确认失败**

在 `frontend/tests/multi-patient-workspace.test.mjs` 添加：

```js
test('医生端不再用扩展百分比表达问诊是否完成', () => {
  const decision = fs.readFileSync(new URL('../src/components/DecisionExplanationPanel.vue', import.meta.url), 'utf8')
  assert.match(decision, /核心诊前资料已完成/)
  assert.match(decision, /已覆盖的主要线索/)
  assert.match(decision, /诊中建议补充/)
  assert.match(decision, /选填资料，不影响诊前档案保存/)
  assert.doesNotMatch(decision, /Number\(layer\.score/)
})
```

Run: `cd frontend && node --test tests/multi-patient-workspace.test.mjs`

Expected: FAIL，因为组件仍显示扩展百分比。

- [ ] **Step 2: 替换扩展资料百分比区块**

在 `DecisionExplanationPanel.vue` 中导入并计算摘要：

```js
import { computed } from 'vue'
import { buildDoctorDecisionSummary } from '../doctor-decision-summary.js'

const decisionSummary = computed(() => buildDoctorDecisionSummary(props.summary?.field_groups || {}))
```

将原 `decision-layer-list` 百分比区块替换为：

```vue
<section class="decision-block">
  <small>已覆盖的主要线索</small>
  <div v-if="decisionSummary.covered.length" class="decision-covered-list">
    <article v-for="item in decisionSummary.covered" :key="item.title">
      <strong>{{ item.title }}</strong>
      <p>{{ item.detail }}</p>
    </article>
  </div>
  <p v-else>当前尚未形成可汇总的扩展线索。</p>
</section>

<section class="decision-block">
  <small>诊中建议补充</small>
  <p class="decision-helper">以下为选填资料，不影响诊前档案保存；请医生结合主诉按需确认。</p>
  <div v-if="decisionSummary.pending.length" class="decision-tags">
    <span v-for="item in decisionSummary.pending" :key="item">{{ item }}</span>
  </div>
  <p v-else>当前无额外诊中补充项。</p>
</section>
```

核心卡片文案改为：

```vue
<p>{{ explanation.core_completed === explanation.core_total ? '核心诊前资料已完成' : '核心诊前资料仍待补充' }}</p>
```

- [ ] **Step 3: 添加简洁样式**

在 `frontend/src/style.css` 添加：

```css
.decision-covered-list { display: grid; gap: 10px; margin-top: 10px; }
.decision-covered-list article { padding: 10px 12px; border-radius: 10px; background: #f6f8fb; }
.decision-covered-list strong { color: #36405b; }
.decision-covered-list p { margin-top: 4px; font-size: 12px; }
```

删除不再使用的 `.decision-layer-list` 样式。

- [ ] **Step 4: 运行前端测试**

Run: `cd frontend && npm.cmd test -- --run`

Expected: 全部测试 PASS。

- [ ] **Step 5: 运行生产构建**

Run: `cd frontend && npm.cmd run build`

Expected: Vite 构建成功，无Vue模板或模块导入错误。

---

### Task 3: 真实医生档案验收

**Files:**
- No code changes expected.

**Interfaces:**
- Consumes: 本地后端 `GET /api/doctor/sessions/{session_id}/summary` 与前端医生工作台。
- Produces: 对真实已完成档案的验收记录。

- [ ] **Step 1: 确认服务运行**

Run: `netstat -ano | Select-String ':3306|:8000|:5173'`

Expected: MySQL、后端和前端端口均处于 LISTENING。

- [ ] **Step 2: 打开医生端并选择已完成档案**

URL: `http://127.0.0.1:5173/?role=doctor`

Expected:

- 顶部显示核心必问项完成数量。
- 不再出现 `43.5%`、`52.5%` 等扩展覆盖百分比。
- 已覆盖线索包含真实问诊中已确认的病程、生活方式和中医症状类别。
- 诊中建议补充以中文标签显示，不出现英文键名。
- 存在胸痛时优先显示线下安全评估提示。

- [ ] **Step 3: 最终回归验证**

Run: `cd frontend && npm.cmd test -- --run && npm.cmd run build`

Expected: 所有测试通过且构建成功。
