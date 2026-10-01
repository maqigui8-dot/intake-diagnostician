# Collapsible Sidebar Visual Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将患者端改造成贴左全高、可完全隐藏且记忆状态的侧栏布局，并统一主工作区卡片与背景视觉。

**Architecture:** 用独立纯函数模块封装侧栏偏好读取与响应式显示规则，`App.vue` 只负责状态和交互编排，`style.css` 负责桌面固定侧栏、折叠浮动操作和移动抽屉。现有问诊流程和 API 行为不变。

**Tech Stack:** Vue 3 Composition API、CSS、localStorage、matchMedia、Node test runner、Vite。

## Global Constraints

- 不新增图标库、图片资源或运行时依赖。
- `localStorage` 键固定为 `intake-sidebar-collapsed`。
- 桌面侧栏宽度约 `280px`，主内容最大宽度约 `960px`。
- `860px` 及以下使用覆盖式移动抽屉。
- 折叠状态不得清空问诊或输入内容。
- 保留继续问诊、已完成档案、软归档和软删除功能。

---

### Task 1: 侧栏偏好纯函数

**Files:**
- Create: `frontend/src/sidebar-state.js`
- Create: `frontend/tests/sidebar-state.test.mjs`

**Interfaces:**
- Produces: `SIDEBAR_STORAGE_KEY`
- Produces: `readSidebarCollapsed(storage) -> boolean`
- Produces: `writeSidebarCollapsed(storage, collapsed) -> void`

- [ ] **Step 1: 写失败测试**

```javascript
test('读取保存的折叠状态且存储失败时安全回退', () => {
  assert.equal(readSidebarCollapsed({ getItem: () => 'true' }), true)
  assert.equal(readSidebarCollapsed({ getItem: () => null }), false)
  assert.equal(readSidebarCollapsed({ getItem: () => { throw new Error('blocked') } }), false)
})
```

再测试写入值只能为字符串 `true` 或 `false`，写入异常不向外抛出。

- [ ] **Step 2: 运行并确认模块缺失导致失败**

```powershell
Set-Location frontend
npm.cmd test
```

- [ ] **Step 3: 实现最小纯函数**

```javascript
export const SIDEBAR_STORAGE_KEY = 'intake-sidebar-collapsed'

export function readSidebarCollapsed(storage) {
  try { return storage?.getItem(SIDEBAR_STORAGE_KEY) === 'true' } catch { return false }
}

export function writeSidebarCollapsed(storage, collapsed) {
  try { storage?.setItem(SIDEBAR_STORAGE_KEY, String(Boolean(collapsed))) } catch {}
}
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
npm.cmd test
```

---

### Task 2: Vue 布局和折叠交互

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Consumes: `readSidebarCollapsed`、`writeSidebarCollapsed`
- Produces: `sidebarCollapsed`、`mobileSidebarOpen`
- Produces: `collapseSidebar()`、`expandSidebar()`、`closeMobileSidebar()`

- [ ] **Step 1: 写结构失败测试**

断言旧顶栏移除，并存在：

```javascript
assert.doesNotMatch(template, /class="topbar"/)
assert.match(template, /class="sidebar-brand"/)
assert.match(template, /aria-label="收起侧栏"/)
assert.match(template, /aria-label="展开侧栏"/)
assert.match(template, /class="sidebar-backdrop"/)
assert.match(appSource, /readSidebarCollapsed\(window\.localStorage\)/)
assert.match(appSource, /writeSidebarCollapsed\(window\.localStorage/)
```

- [ ] **Step 2: 运行测试确认因新布局缺失而失败**

```powershell
npm.cmd test
```

- [ ] **Step 3: 重组模板并实现状态**

根节点增加 `sidebar-collapsed` 与 `mobile-sidebar-open` class。将品牌和用户信息移入 `aside`，侧栏外增加：

```vue
<div v-if="sidebarCollapsed || isMobile" class="floating-shell-actions">
  <button aria-label="展开侧栏" @click="expandSidebar">展开</button>
  <button @click="restart">+ 新建问诊</button>
</div>
<button v-if="mobileSidebarOpen" class="sidebar-backdrop" aria-label="关闭侧栏" @click="closeMobileSidebar"></button>
```

监听 `(max-width: 860px)`，移动端展开使用 `mobileSidebarOpen`，桌面端切换写入 `localStorage`。移动端选择记录或新建后关闭抽屉。

- [ ] **Step 4: 运行前端测试确认通过**

```powershell
npm.cmd test
```

---

### Task 3: 全高侧栏和主工作区视觉

**Files:**
- Modify: `frontend/src/style.css`
- Modify: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Consumes: App 根节点状态 class
- Produces: 桌面固定侧栏、折叠布局、移动抽屉、统一工作卡片

- [ ] **Step 1: 写 CSS 失败测试**

```javascript
assert.match(styleSource, /\.left-panel\s*\{[^}]*position:\s*fixed[^}]*height:\s*100vh/s)
assert.match(styleSource, /\.sidebar-collapsed\s+\.main-workspace/s)
assert.match(styleSource, /\.floating-shell-actions/s)
assert.match(styleSource, /\.sidebar-backdrop/s)
assert.match(styleSource, /@media \(max-width: 860px\)/)
```

- [ ] **Step 2: 运行测试并确认因样式缺失而失败**

```powershell
npm.cmd test
```

- [ ] **Step 3: 实现桌面与移动样式**

主要规则：

```css
.left-panel { position: fixed; inset: 0 auto 0 0; width: 280px; height: 100vh; }
.main-workspace { margin-left: 280px; min-height: 100vh; }
.sidebar-collapsed .main-workspace { margin-left: 0; }
.main-panel { width: min(960px, calc(100% - 64px)); margin: 0 auto; }
```

侧栏使用 `display:flex; flex-direction:column`，记录区滚动；患者工作区统一白色 `18px` 圆角卡片和柔和阴影；聊天输入区、表单控件和按钮统一圆角。

移动端将侧栏改为 `transform` 抽屉并增加遮罩；工作卡片宽度改为 `calc(100% - 24px)`。

- [ ] **Step 4: 运行测试和生产构建**

```powershell
npm.cmd test
npm.cmd run build
```

---

### Task 4: 全量回归和浏览器视觉验收

**Files:**
- Verify: `frontend/src/App.vue`
- Verify: `frontend/src/style.css`
- Verify: `frontend/src/sidebar-state.js`

**Interfaces:**
- Consumes: Tasks 1-3 全部成果
- Produces: 可交付的桌面与移动布局

- [ ] **Step 1: 运行全量自动化验证**

```powershell
Set-Location backend
python -m unittest discover -s tests -p "test_*.py"
Set-Location ../frontend
npm.cmd test
npm.cmd run build
```

- [ ] **Step 2: 桌面展开态验收**

浏览器使用约 `1440×900`：确认侧栏贴左全高、无旧顶栏、主卡片居中、历史操作可用。

- [ ] **Step 3: 桌面折叠与记忆验收**

点击收起：确认侧栏完全消失，只显示展开和新建按钮；刷新页面，确认仍保持折叠；再次展开，确认内容未丢失。

- [ ] **Step 4: 手机抽屉验收**

浏览器使用约 `390×844`：确认默认无侧栏占位、展开后有抽屉和遮罩、点击遮罩关闭、页面无横向溢出。

