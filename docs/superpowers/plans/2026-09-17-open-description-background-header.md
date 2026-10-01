# Open Description Background Header Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让开放描述介绍区融入页面背景，并让白色卡片从具体问题开始。

**Architecture:** 将开放描述模板拆为背景化 `.open-intake-header` 和卡片化 `.open-question`。保留 `.open-intake` 作为透明布局容器，仅通过局部 CSS 改变视觉层级，不触碰业务状态。

**Tech Stack:** Vue 3、CSS、Node.js Test Runner、Vite

## Global Constraints

- 现有文案和交互逻辑保持不变。
- 不增加图标或明显分割线。
- 桌面端和移动端不得横向溢出。

---

### Task 1: 背景化开放描述介绍区

**Files:**
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Consumes: `open-intake-identity`、`open-intake-heading`、`open-question`
- Produces: `.open-intake-header` 背景区与独立白色 `.open-question` 卡片

- [ ] **Step 1: Write the failing test**

```js
test('开放描述介绍区融入背景且具体问题使用独立白色卡片', () => {
  assert.match(template, /class="open-intake-header"[\s\S]*?open-intake-identity[\s\S]*?open-intake-heading/)
  assert.match(styleSource, /\.open-intake\s*\{[^}]*background:\s*transparent/s)
  assert.match(styleSource, /\.open-question\s*\{[^}]*background:\s*rgba?\(/s)
})
```

- [ ] **Step 2: Run focused test and verify failure**

Run: `npm.cmd test -- --test-name-pattern="介绍区融入背景"`

Expected: FAIL，因为 `.open-intake` 当前仍共享白色卡片样式。

- [ ] **Step 3: Implement template grouping and CSS**

```vue
<div class="open-intake-header">
  <div class="assistant-intro open-intake-identity">...</div>
  <div class="open-intake-heading">...</div>
</div>
<div class="open-question">...</div>
```

```css
.open-intake { padding: 0; background: transparent; border: 0; box-shadow: none; }
.open-question { margin-top: 24px; padding: 32px 40px; background: rgba(255,255,255,.94); border: 1px solid rgba(55,100,80,.12); border-radius: 18px; box-shadow: 0 18px 45px rgba(35,67,53,.08); }
```

- [ ] **Step 4: Run complete verification**

Run: `npm.cmd test`

Expected: 43 tests PASS，0 failures。

Run: `npm.cmd run build`

Expected: Vite build exits with code 0。

- [ ] **Step 5: Visual verification**

检查桌面端与 390px 移动端：标题直接位于浅绿色背景，具体问题从白色卡片开始，无横向溢出。

- [ ] **Step 6: Commit**

项目不是 Git 仓库，不执行提交；保留修改文件供用户检查。
