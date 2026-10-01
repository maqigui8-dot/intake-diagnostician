# Open Question and Sidebar Density Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 压缩开放问题卡片高度，并降低侧栏流程区域的信息密度。

**Architecture:** 新增 `visibleHistoryRecords` 计算属性限制侧栏渲染数量；把当前问诊放弃按钮移动到 `sidebar-footer`。所有视觉调整均通过现有类名和局部 CSS 完成，不修改 API。

**Tech Stack:** Vue 3、CSS、Node.js Test Runner、Vite

## Global Constraints

- 历史档案总数徽标仍显示完整数量。
- 侧栏最多渲染最近两条已完成档案。
- 不改变归档、删除和提交逻辑。
- 不调整背景化标题区和主内容宽度。

---

### Task 1: 压缩问题卡片并整理侧栏层级

**Files:**
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Consumes: `historyRecords: Ref<Array>`、`canArchiveCurrent`、`.open-question`
- Produces: `visibleHistoryRecords: ComputedRef<Array>`、底部 `.sidebar-current-action`

- [ ] **Step 1: Write the failing tests**

```js
test('侧栏已完成档案最多渲染最近两条且放弃操作位于底部', () => {
  assert.match(template, /v-for="record in visibleHistoryRecords"/)
  assert.match(appSource, /const visibleHistoryRecords = computed\(\(\) => historyRecords\.value\.slice\(0, 2\)\)/)
  assert.match(template, /class="sidebar-footer"[\s\S]*?class="archive-current-link sidebar-current-action"/)
})

test('开放问题卡片使用更紧凑的排版', () => {
  assert.match(styleSource, /\.open-question textarea\s*\{[^}]*min-height:\s*168px/s)
  assert.match(styleSource, /\.open-question h3\s*\{[^}]*font-size:\s*19px/s)
})
```

- [ ] **Step 2: Verify tests fail**

Run: `npm.cmd test -- --test-name-pattern="侧栏已完成档案|开放问题卡片"`

Expected: 2 failures because the computed list, footer placement and compact sizes do not exist.

- [ ] **Step 3: Implement the template and computed list**

```js
const visibleHistoryRecords = computed(() => historyRecords.value.slice(0, 2))
```

将档案循环改为 `visibleHistoryRecords`，并将 `archive-current-link` 按钮移动到 `sidebar-footer` 首位，追加 `sidebar-current-action` 类名。

- [ ] **Step 4: Implement compact CSS**

```css
.open-question h3 { font-size: 19px; }
.open-question textarea { min-height: 168px; }
.open-question { padding-top: 26px; padding-bottom: 26px; }
.sidebar-current-action { margin: 0; padding: 8px 4px; color: #927067; }
.left-panel-edit { font-size: 11px; font-weight: 600; }
.composer-actions small { color: #89968f; font-size: 11px; }
```

- [ ] **Step 5: Run complete verification**

Run: `npm.cmd test`

Expected: 45 tests PASS，0 failures。

Run: `npm.cmd run build`

Expected: Vite build exits with code 0。

- [ ] **Step 6: Visual verification**

检查桌面端与 390px 移动端，确认问题卡片更紧凑、放弃操作位于底部、侧栏最多显示两条档案且无溢出。

- [ ] **Step 7: Commit**

项目不是 Git 仓库，不执行提交；保留修改文件供用户检查。
