# 中医诊前问诊系统汇报 PPT 重做 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 使用 5 张项目实机截图制作一份 7 页、可直接汇报的中文 PPTX。

**Architecture:** 使用 ppt-master 的 SVG 主流程。先锁定设计规范和图片资源，再由当前主代理逐页手写 SVG，完成质量检查、讲稿生成、后处理和 PPTX 导出。

**Tech Stack:** ppt-master、SVG、PowerPoint DrawingML、Python 辅助检查脚本。

## Global Constraints

- 画布固定为 `1280 × 720`。
- 每个 SVG 根元素必须包含 `width`、`height` 和 `viewBox`。
- 5 张项目截图均使用 `preserveAspectRatio="xMidYMid meet"`，不得拉伸。
- 不使用 AI 生成图片或网络图片。
- 不覆盖旧版 PPT，最终文件另存到 `ppt-output/`。

---

### Task 1: 素材与设计锁定

**Files:**
- Create: `projects/tcm-intake-user-flow-2026-08-13_ppt169_20260813/design_spec.md`
- Create: `projects/tcm-intake-user-flow-2026-08-13_ppt169_20260813/spec_lock.md`
- Create: `projects/tcm-intake-user-flow-2026-08-13_ppt169_20260813/sources/requirements.md`

- [ ] 分析 5 张截图尺寸并记录到 `analysis/image_analysis.csv`。
- [ ] 写入 7 页内容大纲、配色、字体、图标和图片映射。
- [ ] 同步并验证 `tabler-outline` 图标库存。

### Task 2: 逐页生成 SVG

**Files:**
- Create: `svg_output/01_cover.svg` 至 `svg_output/07_outputs.svg`

- [ ] 启动实时预览服务。
- [ ] 每页生成前重新读取 `spec_lock.md`。
- [ ] 按 P01 至 P07 顺序手写 SVG，不批量脚本生成。
- [ ] 每张截图按设计规范的页面和原比例嵌入。

### Task 3: 质量检查与讲稿

**Files:**
- Create: `notes/total.md`
- Generate: `notes/01_cover.md` 至 `notes/07_outputs.md`

- [ ] 运行 `svg_quality_checker.py`，预期 7 页全部通过且 0 错误。
- [ ] 渲染 7 页截图并逐页检查图片清晰度、文字换行和元素重叠。
- [ ] 为每页写 40–70 秒中文讲稿并拆分为一一对应的备注文件。

### Task 4: 后处理和导出

**Files:**
- Generate: `svg_final/*.svg`
- Generate: `exports/*.pptx`
- Deliver: `ppt-output/中医诊前问诊系统-问题改进与完整使用流程-2026-08-13.pptx`

- [ ] 运行 `finalize_svg.py`。
- [ ] 运行 `svg_to_pptx.py`，预期 7 页全部成功并嵌入 7 页讲稿。
- [ ] 检查 PPTX ZIP 完整性、页数、备注数和 SVG 根尺寸。
