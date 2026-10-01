# 项目汇报 PPT 重做实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于已确认的 14 页内容，制作一套更适合组会汇报、视觉层级更清晰的学术汇报型 PPT。

**Architecture:** 继续使用 PPT Master 的 SVG 主流程。先建立独立的重做项目并锁定视觉规范，再由主代理逐页手写 14 个 SVG，加入演讲备注，完成质量检查、后处理、PPTX 导出和兼容版导出。

**Tech Stack:** PPT Master、SVG、PowerPoint PPTX、Chrome 无界面渲染、Artifact Tool 兼容封装。

## Global Constraints

- 固定 14 页，标题与顺序保持不变。
- 背景 `#F7F5EF`，主色 `#155348`，强调色 `#C86A3A`。
- 字体使用微软雅黑，除封面外标题位于左上角。
- 禁止渐变、阴影、图标堆叠和大面积卡片网格。
- P12 至 P14 保留截图位置。
- SVG 必须由主代理逐页手写，不能使用批量生成脚本。

---

### Task 1: 建立重做项目和执行锁

**Files:**
- Create: `projects/project_report_redesign_ppt169_20260918/design_spec.md`
- Create: `projects/project_report_redesign_ppt169_20260918/spec_lock.md`

- [ ] 建立独立项目目录，不覆盖旧版。
- [ ] 将确认的视觉设计和 14 页内容写入设计规范。
- [ ] 锁定画布、配色、字体、页面节奏和机制图映射。
- [ ] 检查规范不存在未确定项或与设计文档冲突的要求。

### Task 2: 生成 P01 至 P05

**Files:**
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/01_cover.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/02_background.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/03_goal.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/04_architecture.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/05_roles.svg`

- [ ] 每页生成前重新读取 `spec_lock.md`。
- [ ] 依次完成封面、问题页、目标页、四层架构和双角色数据流。
- [ ] 每页只设置一个主要视觉中心。
- [ ] 检查标题位置、正文大小和安全边距。

### Task 3: 生成 P06 至 P11

**Files:**
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/06_flow.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/07_fields.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/08_completeness.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/09_priority.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/10_stop.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/11_challenges.svg`

- [ ] 依次完成反馈式问诊流程、字段来源链路、完整度判断器、优先级阶梯、停止判断树和难点状态页。
- [ ] 使用陶土橙标记风险、决策和流程转折。
- [ ] 避免将机制内容重新画成文字表格。
- [ ] 确保完整度、问题来源和停止条件是全套视觉重点。

### Task 4: 生成 P12 至 P14

**Files:**
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/12_demo_patient.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/13_demo_flow.svg`
- Create: `projects/project_report_redesign_ppt169_20260918/svg_output/14_demo_doctor.svg`

- [ ] 完成主截图加局部截图的身份选择页。
- [ ] 完成三阶段视觉推进的问诊过程页。
- [ ] 完成医生工作台大截图和三项注释的总结页。
- [ ] 使用实线细框和编号替代虚线线框稿样式。

### Task 5: 演讲备注与 SVG 质量检查

**Files:**
- Create: `projects/project_report_redesign_ppt169_20260918/notes/total.md`

- [ ] 为 14 页编写中文演讲备注。
- [ ] 运行 `svg_quality_checker.py`。
- [ ] 修复全部错误和可直接修复的警告。
- [ ] 确认 14 个 SVG 与 14 段备注一一对应。

### Task 6: 导出和兼容性验证

**Files:**
- Create: `projects/project_report_redesign_ppt169_20260918/exports/project_report_redesign.pptx`
- Create: `projects/project_report_redesign_ppt169_20260918/exports/project_report_redesign_compatible.pptx`

- [ ] 依次运行备注拆分、SVG 后处理和 PPTX 导出。
- [ ] 将最终 SVG 渲染为 14 张 1280×720 PNG。
- [ ] 使用标准图片型 PPTX 容器生成兼容版并保留演讲备注。
- [ ] 验证两个文件的页数、备注数、媒体数和包结构。
- [ ] 渲染兼容版全部页面，确认页面数量和视觉输出完整。

## 自检

- 设计规范中的页面全部被任务覆盖。
- 无 TBD、TODO 或未定义的交付文件。
- 文件名、页数、颜色和兼容版要求前后一致。
