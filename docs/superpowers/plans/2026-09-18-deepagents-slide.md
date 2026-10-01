# DeepAgents 中医复诊智能体新增页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有《前期学习与项目实践汇报》中新增一页 DeepAgents 中医复诊智能体实践页，并预留大尺寸运行截图位置。

**Architecture:** 读取原 31 页 PPT 的页面尺寸和第 13—20 页 Agent 视觉风格，创建与原风格一致的新页面，再将其插入原第 19 页之后。最后导出新的 32 页 PPTX，渲染新增页和整套缩略图进行检查。

**Tech Stack:** PowerPoint PPTX、`@oai/artifact-tool`、presentations 渲染与结构验证工具。

## Global Constraints

- 不覆盖原始《前期学习与项目实践汇报.pptx》文件。
- 新增页插在原第 19 页之后，最终共 32 页。
- 米白背景、深绿色和橙色与原 Agent 部分一致。
- 右侧保留约一半页面用于替换运行截图。
- 页面明确标注学习与原型验证边界。

---

### Task 1: 提取原 PPT 视觉参数

**Files:**
- Read: `presentations/前期学习与项目实践汇报.pptx`
- Create: `projects/deepagents_slide_20260918/`

- [ ] 检查页面比例、主色、标题位置、字号和页码样式。
- [ ] 以原 Agent 页为视觉依据，记录新增页的固定网格。

### Task 2: 制作 DeepAgents 新增页

**Files:**
- Create: `projects/deepagents_slide_20260918/build_slide.mjs`

- [ ] 创建标题“基于 DeepAgents 构建中医复诊智能体”。
- [ ] 左侧加入工作链路和三项实现要点。
- [ ] 右侧加入大尺寸截图占位框和截图说明位置。
- [ ] 底部加入“学习与原型验证，不替代医生诊断或临床决策”。

### Task 3: 插入并导出 32 页版本

**Files:**
- Create: `presentations/前期学习与项目实践汇报_DeepAgents新增页.pptx`

- [ ] 将新增页插入原第 19 页之后。
- [ ] 保持其他 31 页内容与顺序不变。
- [ ] 更新新增页页码并导出 PPTX。

### Task 4: 验证与交付

**Files:**
- Create: `projects/deepagents_slide_20260918/rendered/`
- Create: `projects/deepagents_slide_20260918/montage.png`

- [ ] 运行结构检查，确认最终文件为 32 页。
- [ ] 渲染新增页，检查标题、正文和截图占位没有溢出或遮挡。
- [ ] 生成整套缩略图，确认插入顺序正确。
