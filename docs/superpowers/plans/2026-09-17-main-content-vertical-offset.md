# Main Content Vertical Offset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将桌面端中央主内容下移 30px，同时保持侧栏和移动端布局不变。

**Architecture:** 仅调整现有 `.main-workspace` 的桌面端顶部内边距，通过现有移动端媒体查询继续覆盖为 `76px`。用静态样式测试锁定桌面端和移动端两个数值。

**Tech Stack:** Vue 3、CSS、Node.js Test Runner、Vite

## Global Constraints

- 桌面端 `.main-workspace` 顶部内边距必须为 `70px`。
- `860px` 以下移动端顶部内边距必须保持 `76px`。
- 不修改侧栏位置、宽度和折叠逻辑。

---

### Task 1: 调整主内容区垂直位置

**Files:**
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Consumes: `.main-workspace` 和 `@media (max-width: 860px)` 现有样式规则
- Produces: 桌面端 `70px`、移动端 `76px` 的稳定顶部间距

- [ ] **Step 1: Write the failing test**

```js
test('桌面端主内容下移且移动端顶部间距保持不变', () => {
  assert.match(styleSource, /\.main-workspace\s*\{[^}]*padding:\s*70px clamp\(24px, 4vw, 64px\)/s)
  assert.match(styleSource, /@media \(max-width: 860px\)[\s\S]*?padding:\s*76px 12px 24px/s)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm.cmd test -- --test-name-pattern="桌面端主内容下移"`

Expected: FAIL，因为桌面端当前仍为 `40px`。

- [ ] **Step 3: Write minimal implementation**

```css
.main-workspace {
  padding: 70px clamp(24px, 4vw, 64px);
}
```

- [ ] **Step 4: Run tests and build**

Run: `npm.cmd test`

Expected: 40+ tests PASS，0 failures。

Run: `npm.cmd run build`

Expected: Vite build exits with code 0。

- [ ] **Step 5: Visual verification**

在本地浏览器重新加载 `http://127.0.0.1:5173/`，确认桌面主卡片下移、侧栏仍位于 `left: 0`，并检查移动端顶部间距未改变。

- [ ] **Step 6: Commit**

项目当前不是 Git 仓库，因此不执行提交；保留修改文件供用户检查。
