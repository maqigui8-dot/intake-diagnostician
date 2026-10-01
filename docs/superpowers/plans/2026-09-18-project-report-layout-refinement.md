# 项目汇报 PPT 第二轮版式优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变 14 页汇报结构和项目事实的前提下，提高字号与可读性，重做项目目标和完整问诊流程，并输出可编辑版与兼容版。

**Architecture:** 在现有 Artifact Tool 原生对象构建脚本上修改，保留统一的基础版式函数，同时为叙事页增加开放式布局。先生成原生可编辑 PPTX，再渲染成 PNG 进行视觉检查，最后生成图片型兼容备用版。

**Tech Stack:** JavaScript ES modules、`@oai/artifact-tool`、PowerPoint PPTX、Python `python-pptx`（仅用于兼容备用版）、presentations 渲染与结构验证工具。

## Global Constraints

- 保持现有 14 页结构、内容顺序、配色和 16:9 页面比例。
- 标题位于左上角；标题下方使用严格水平的橙色短线和浅灰色长线。
- 正文原则上不低于 18 pt，说明性小字不低于 15 pt。
- 第 3 页重写为四个易懂、可讲解的项目目标。
- 第 6 页保留业务逻辑，改成包含判断分支的开放式流程。
- 主版本中的文字、线条和流程元素必须可编辑。

---

### Task 1: 全局字号与标题装饰线

**Files:**
- Modify: `projects/project_report_regular_ppt169_20260918/native_build/build_editable.mjs`

**Interfaces:**
- Consumes: `base(titleText, no)`、`text(...)`、统一颜色常量 `C`。
- Produces: 所有内容页共享的水平标题线与提高后的字号体系。

- [ ] **Step 1: 修正基础版式**

将 `base()` 中装饰线改为同一纵坐标上的橙色短线和浅灰长线，避免对角线几何对象；保留统一页码与底部分隔线。

- [ ] **Step 2: 调整字号**

检查 14 页文字对象，将主要正文提升至 18—21 pt，将说明文字控制在 15—17 pt；内容溢出时优先精简文案或扩大文本区域，不以缩小字号解决。

- [ ] **Step 3: 生成草稿并验证语法**

Run: `node --check projects/project_report_regular_ppt169_20260918/native_build/build_editable.mjs`

Expected: exit code 0。

### Task 2: 重做项目目标页

**Files:**
- Modify: `projects/project_report_regular_ppt169_20260918/native_build/build_editable.mjs`

**Interfaces:**
- Consumes: 第 3 页现有标题与项目能力边界。
- Produces: 四个目标及其结果说明，使用开放式中心定位布局。

- [ ] **Step 1: 替换项目目标文案**

使用以下四项目标：

1. 信息结构化：把患者自然描述整理为症状、时间、生活方式与安全信息等字段。
2. 有目的追问：依据缺失的核心字段选择下一项问题，避免无关或重复提问。
3. 及时停止：核心资料可用时正常结束；无法继续采集或出现风险时保护性结束。
4. 结果可追溯：保存原始回答、字段来源、判断依据和最终诊前档案。

- [ ] **Step 2: 建立开放式版式**

使用中心定位语句连接四项目标，减少完全相同的矩形卡片；确保四项标题与说明可直接阅读。

- [ ] **Step 3: 渲染第 3 页检查**

Run: `render_slides.py <editable-pptx> --output_dir <render-dir>`

Expected: 第 3 页无文字溢出，四项目标的动作与结果均完整显示。

### Task 3: 重做完整问诊流程页

**Files:**
- Modify: `projects/project_report_regular_ppt169_20260918/native_build/build_editable.mjs`

**Interfaces:**
- Consumes: 患者表达、信息提取、完整度判断、继续追问、生成档案的既有业务逻辑。
- Produces: 一条清晰主流程和一个双分支判断节点。

- [ ] **Step 1: 调整信息层级**

将主流程定义为“患者表达—信息提取—完整度判断”，在判断节点后分为“继续追问”和“生成档案”；字段更新、证据记录等内容作为次级说明放在对应节点下方。

- [ ] **Step 2: 调整视觉结构**

采用较大的编号节点、水平连线和上下分支，减少七个同权重方框；保留足够留白并突出完整度判断。

- [ ] **Step 3: 渲染第 6 页检查**

Expected: 汇报者能够按视觉顺序讲清主流程，观众能够看出判断后的两种结果。

### Task 4: 统一其他页面与截图占位

**Files:**
- Modify: `projects/project_report_regular_ppt169_20260918/native_build/build_editable.mjs`

**Interfaces:**
- Consumes: 第 2、4、5、7—14 页现有内容。
- Produces: 字号统一、边框减少、重点页突出、截图区域主次清楚的 14 页完整稿。

- [ ] **Step 1: 调整第 2、4、5、7—11 页**

放大正文并减少不必要边框；保留第 8 页完整度判断和第 10 页停止追问的重点视觉层级。

- [ ] **Step 2: 调整第 12—14 页**

保留截图位置，第 12 页使用一张主截图和两张辅助截图，第 13 页使用三阶段截图，第 14 页使用医生端主截图与三项讲解提示。

- [ ] **Step 3: 生成可编辑版**

Run: `node projects/project_report_regular_ppt169_20260918/native_build/build_editable.mjs`

Expected: `exports/project_report_regular_editable_v2.pptx` 生成成功。

### Task 5: 渲染、修复与兼容版本

**Files:**
- Modify: `projects/project_report_regular_ppt169_20260918/native_build/build_compatible.py`
- Create: `projects/project_report_regular_ppt169_20260918/exports/project_report_regular_editable_v2.pptx`
- Create: `projects/project_report_regular_ppt169_20260918/exports/project_report_regular_compatible_v2.pptx`

**Interfaces:**
- Consumes: 最终可编辑 PPTX 与 14 张渲染图。
- Produces: 两个可交付文件和可视化检查证据。

- [ ] **Step 1: 渲染全部 14 页并生成拼图**

Expected: 14 张 PNG 全部生成，拼图中无重叠、截断、倾斜标题线或异常留白。

- [ ] **Step 2: 放大检查关键页**

检查第 3、6、8、10、12—14 页，发现问题后回到构建脚本修复并重新渲染。

- [ ] **Step 3: 生成兼容备用版**

更新 `build_compatible.py`，使用新版 14 张渲染图生成 `project_report_regular_compatible_v2.pptx`。

- [ ] **Step 4: 完整性验证**

分别对两个 PPTX 运行 `inspect_presentation_package_integrity.py`，再渲染兼容版。

Expected: 两个文件均为 14 页，结构检查 `status: pass`，兼容版成功渲染 14 张 PNG；可编辑版包含原生文本和图形对象。
