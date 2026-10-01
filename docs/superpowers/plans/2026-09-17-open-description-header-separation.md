# Open Description Header Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将开放描述页的阶段身份区与正文提问区拆分为两个独立视觉层级。

**Architecture:** 在现有 `open-intake` 内保留 `assistant-intro` 作为身份区，新建 `open-intake-heading` 承载标题与说明。输入区和业务逻辑不变，仅补充局部 CSS。

**Tech Stack:** Vue 3、CSS、Node.js Test Runner、Vite

## Global Constraints

- 文案保持原样。
- 只修改开放描述首屏。
- 不增加图标，不改变业务逻辑。

---

### Task 1: 拆分开放描述标题层级

**Files:**
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Consumes: `viewStage === 'open_intake'` 模板和 `assistant-intro` 样式
- Produces: 独立的 `.open-intake-identity` 与 `.open-intake-heading` 区块

- [ ] **Step 1: Write the failing test**

```js
test('开放描述页将阶段身份与正文标题拆为独立区块', () => {
  const openIntake = template.match(/viewStage === 'open_intake'[\s\S]*?(?=<section v-else-if)/)?.[0] || ''
  assert.match(openIntake, /class="assistant-intro open-intake-identity"[\s\S]*?开放描述[\s\S]*?<\/div>\s*<div class="open-intake-heading">/)
})
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `npm.cmd test -- --test-name-pattern="阶段身份与正文标题"`

Expected: FAIL，因为标题当前仍嵌套在 `assistant-intro` 中。

- [ ] **Step 3: Implement the minimal template and CSS change**

```vue
<div class="assistant-intro open-intake-identity">
  <span class="assistant-avatar">医</span>
  <span class="section-label">开放描述</span>
</div>
<div class="open-intake-heading">
  <h2>先从您最关心的情况说起</h2>
  <p>不需要使用医学术语，按自己的感受描述即可。</p>
</div>
```

```css
.open-intake-identity { align-items: center; padding-bottom: 18px; }
.open-intake-heading { padding-top: 24px; }
```

- [ ] **Step 4: Run all tests and production build**

Run: `npm.cmd test`

Expected: 42 tests PASS，0 failures。

Run: `npm.cmd run build`

Expected: Vite build exits with code 0。

- [ ] **Step 5: Verify visually**

刷新本地项目，确认两个区块的边界、桌面端间距和移动端无溢出。

- [ ] **Step 6: Commit**

项目当前不是 Git 仓库，不执行提交；保留修改文件供用户查看。
