# 项目汇报标准答辩型 PPT 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 制作一套 14 页、版式规整统一、适合组会汇报且能在 PowerPoint/WPS 中打开和编辑的项目汇报 PPT。

**Architecture:** 先使用 PPT Master 逐页生成规整的 SVG 视觉源稿，再用 Artifact Tool 按相同坐标重建标准 PowerPoint 原生文本和图形。图片兼容版仅作为备用，不作为正式可编辑交付。

**Tech Stack:** PPT Master、SVG、Artifact Tool、PowerPoint OOXML、Chrome 渲染。

## Global Constraints

- 固定 14 页，标题、顺序和内容范围不变。
- 画布为 1280×720，16:9。
- 背景 `#F7F5EF`，主色 `#155348`，强调色 `#C86A3A`。
- 内容页统一标题栏、横线、内容起始高度和右下角页码。
- 只使用左右双栏、上下分区、三栏并列、标准流程图和标准表格式信息。
- 不使用杂志式错落排版、阴影、渐变或不规则大圆形构图。
- 正式版必须包含原生可编辑文字与图形，不能是整页图片。

---

### Task 1: 建立第三版项目与固定网格

**Files:**
- Create: `projects/project_report_regular_ppt169_20260918/design_spec.md`
- Create: `projects/project_report_regular_ppt169_20260918/spec_lock.md`

- [ ] 初始化独立 PPT Master 项目。
- [ ] 锁定标题栏、正文区、页脚和五种允许版式。
- [ ] 写入 14 页内容映射和截图占位规则。

### Task 2: 生成 14 页规整 SVG 源稿

**Files:**
- Create: `projects/project_report_regular_ppt169_20260918/svg_output/01_cover.svg`
- Create: `projects/project_report_regular_ppt169_20260918/svg_output/02_background.svg` 至 `14_demo_doctor.svg`

- [ ] 逐页读取 `spec_lock.md`。
- [ ] 按统一标题栏和内容网格生成 P01 至 P14。
- [ ] 确保流程节点、表格行、分栏边界和截图框尺寸一致。
- [ ] 运行 SVG 质量检查并修复全部错误。

### Task 3: 演讲备注与 PPT Master 导出

**Files:**
- Create: `projects/project_report_regular_ppt169_20260918/notes/total.md`
- Create: `projects/project_report_regular_ppt169_20260918/exports/project_report_regular_reference.pptx`

- [ ] 写入 14 页中文演讲备注。
- [ ] 依次拆分备注、后处理 SVG、导出参考 PPTX。
- [ ] 渲染全部页面检查视觉一致性。

### Task 4: 标准原生对象重建

**Files:**
- Create: `projects/project_report_regular_ppt169_20260918/native_build/build_editable.mjs`
- Create: `projects/project_report_regular_ppt169_20260918/exports/project_report_regular_editable.pptx`

- [ ] 用 Artifact Tool 创建 14 页标准演示文稿。
- [ ] 将标题、正文、矩形、圆形、线条和箭头重建为原生对象。
- [ ] 嵌入 14 页演讲备注。
- [ ] 运行完整性、页数、字体和版式验证。

### Task 5: 最终验证与备用兼容版

**Files:**
- Create: `projects/project_report_regular_ppt169_20260918/exports/project_report_regular_compatible.pptx`

- [ ] 渲染可编辑版全部 14 页。
- [ ] 检查 14 页、14 份备注、可编辑对象数量和媒体数量。
- [ ] 生成图片兼容版作为备用。
- [ ] 交付时优先提供标准可编辑版。

## 自检

- 14 页内容均有明确版式。
- 正式交付路径不依赖 PPT Master 原生 DrawingML 导出。
- 可编辑性、兼容性和视觉一致性均有独立验证步骤。
- 计划中不存在未确定项。
