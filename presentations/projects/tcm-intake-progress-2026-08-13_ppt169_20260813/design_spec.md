# Design Specification & Content Outline

## I. Project Information

- **Project**: 中医诊前问诊系统阶段进展
- **Purpose**: 对比今天修改前后的产品与技术变化，并说明当前完整流程
- **Audience**: 项目组成员、指导教师与阶段进展汇报听众
- **Language**: 简体中文
- **Page Count**: 6 pages
- **Content Strategy**: balanced default；以今日实际代码改动和验证结果为唯一事实来源
- **Mode**: briefing — 信息完整、结构清楚、便于现场逐页说明
- **Visual Style**: soft-rounded — 延续医疗产品的亲和感，使用适量圆角容器和清晰流程节点

## II. Canvas

- **Format**: PPT 16:9
- **Dimensions**: 1280 × 720
- **ViewBox**: `0 0 1280 720`
- **Safe Margin**: 52px horizontal, 44px vertical

## III. Visual Theme

### Color Scheme

- Background: `#FFFFFF`
- Secondary Background: `#F3F7F5`
- Primary: `#237A57`
- Primary Dark: `#174B39`
- Primary Light: `#DDEEE6`
- Accent / old problem: `#E45B4B`
- Accent Light: `#FBE9E6`
- Secondary Accent: `#D6A83B`
- Secondary Accent Light: `#FBF4DD`
- Body Text: `#1E2A25`
- Secondary Text: `#617068`
- Border: `#D9E4DE`
- Muted: `#A7B3AD`

Color behavior: white and pale green carry most of the canvas; green represents the new stable process, coral identifies old-version problems, and gold highlights important rules or evidence.

## IV. Typography

### Font Plan

| Role | Chinese | English | Fallback tail |
| --- | --- | --- | --- |
| Title | Microsoft YaHei | Arial | sans-serif |
| Body | Microsoft YaHei | Arial | sans-serif |
| Emphasis | Microsoft YaHei | Arial | sans-serif |
| Code | — | Consolas | monospace |

### Per-role font stacks

- Title: `"Microsoft YaHei", Arial, sans-serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: same as Body
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

- Body baseline: 20px
- Cover title: 64px
- Page title: 36px
- Subtitle: 28px
- Hero number: 56px
- Annotation: 14px
- Footer: 12px

Formula policy: text-only; this deck contains no formula-worthy expressions.

## V. Layout Principles

- Header: page title at x=52, y=42; optional section label above or beside it.
- Content: y=112–650, with 24–32px gaps.
- Footer: page number and short project label at y=690.
- Card radius: 14px; pill radius: 18px.
- Dense pages use two-column comparison, horizontal process, or grouped rule blocks.
- Breathing page P03 uses one large conversation mockup as the visual subject rather than a card grid.
- Use native SVG shapes and connectors; no decorative gradients or unrelated imagery.

## VI. Icon Usage Specification

- Library: `tabler-outline`
- Stroke width: `2`
- Usage: single-color line icons inside small circles or beside section labels.

| Purpose | Icon Path | Page |
| --- | --- | --- |
| 对话式追问 | `tabler-outline/message-circle` | P01, P03 |
| 原版问题 | `tabler-outline/alert-circle` | P02 |
| 今日完成 | `tabler-outline/checks` | P02, P06 |
| 当前流程 | `tabler-outline/route` | P04 |
| 完整度判断 | `tabler-outline/list-check` | P04, P05 |
| 问法生成 | `tabler-outline/brain` | P04, P05 |
| 循环重分析 | `tabler-outline/repeat` | P04, P05 |
| 安全保护 | `tabler-outline/shield-check` | P05, P06 |
| 档案输出 | `tabler-outline/file-check` | P04 |
| 接口与策略 | `tabler-outline/settings` | P02 |
| 前后对比 | `tabler-outline/arrows-exchange` | P02 |
| 测试验证 | `tabler-outline/clipboard-check` | P06 |

## VII. Visualization Reference List

No catalog chart template is required. All visualizations are project-specific native SVG infographics: before/after comparison, conversation mockup, process flow, skill handoff, and validation dashboard.

Runners-up considered:

- timeline_horizontal — rejected because the main flow contains a decision loop rather than a purely chronological sequence.
- process_flow_steps — rejected because the current process needs an explicit loop-back and four different stop conditions.
- comparison_matrix — rejected because the old/new comparison is clearer as two asymmetrical sides connected by a central transformation arrow.

## VIII. Image Resource List

No raster images. The deck uses editable native SVG diagrams and synchronized line icons so the change logic remains legible and editable in PowerPoint.

## IX. Content Outline

### Part 1: 今日变化与当前流程

#### Slide 01 - Cover

- **Cover impact**: 一条从“卡片式追问”转向“对话式闭环”的主线，使用左旧右新的对话形态与中央箭头构成视觉钩子。
- **Layout**: 大标题居左，右侧为由单一问题卡转向多轮聊天气泡的抽象示意。
- **Title**: 中医诊前问诊系统
- **Subtitle**: 今日改造对比与当前完整流程
- **Info**: 阶段进展汇报 · 2026.08.13

#### Slide 02 - 原版本与今日新版

- **Layout**: 左右对比，中部使用转换箭头；底部总结今日修改覆盖的五个层面。
- **Title**: 原版本与今日新版
- **Core message**: 对比交互、判断、数据、收敛和验证五个层面的变化。
- **Content**:
  - 原版本：问题卡片、内部字段可能外露、仅有问题文本、可能重复、没有安全边界。
  - 今日新版：对话历史、内部判断隐藏、稳定 key 与类型、重复缺口停止、12 轮后台兜底。
  - 修改范围：前端交互 / 后端策略 / 两个 Skill / 智能分析协议 / 自动化测试。

#### Slide 03 - 对话式追问改造

- **Layout**: 左侧窄栏解释“原来”，右侧大面积聊天界面展示“现在”；突出一问一答和历史连续性。
- **Title**: 对话式追问改造
- **Core message**: 补充问诊从单张问题卡变为保留上下文的连续聊天体验。
- **Content**:
  - 独立追问页面。
  - 历史问题和回答持续可见。
  - 每轮只问一个信息点。
  - 患者只看到自然问题，不看到内部缺口清单。

#### Slide 04 - 当前完整业务流程

- **Layout**: 横向主流程加下方分析回路，使用 7 个节点和 4 个结束条件。
- **Title**: 当前完整业务流程
- **Core message**: 从基础十题到档案和检查建议的完整闭环。
- **Content**:
  - 基础十题 → 提交基础资料 → 完整度判断。
  - 缺关键必问项 → 生成一个自然问题与稳定 key → 对话回答 → 保存 → 重新分析。
  - 信息足够、只剩选问项、重复缺口或达到安全边界 → 输出档案与推荐检查 → 保存记录。

#### Slide 05 - 两个 Skill 与追问收敛

- **Layout**: 上半部双 Skill 分工，下半部收敛规则带。
- **Title**: 两个 Skill 与追问收敛
- **Core message**: 一个 Skill 决定问什么，另一个 Skill 决定怎样问，策略层保证一定结束。
- **Content**:
  - tcm-intake-checklist：区分关键必问项和建议选问项，判断资料是否够用。
  - tcm-questioning-guide：把最重要缺口转成自然、单一问点的问题。
  - 稳定 follow_up_key、required/optional 类型、已问 key 去重、12 轮后台兜底。

#### Slide 06 - 修复结果与验证

- **Closing impact**: 用“12 / 13 / 31 / 15”四个大数字结束，明确无限追问已经被流程级修复，而非依赖模型自觉停止。
- **Layout**: 四个数字证据横排，底部为完成项与下一步。
- **Title**: 修复结果与验证
- **Core message**: 高轮次追问、重复缺口、选问项阻塞和页面显示均已得到验证。
- **Content**:
  - 12：第 12 个回答可正常保存。
  - 13：第 13 次提交返回 400，不再继续。
  - 31：后端测试全部通过。
  - 15：前端测试全部通过。
  - 生产构建通过，页面无控制台错误。

## X. Speaker Notes Requirements

- 每页 45–70 秒，总时长约 6 分钟。
- 用“原来是什么、今天改了什么、现在如何工作、如何证明有效”作为口头主线。
- 技术字段只解释作用，不展开代码实现细节。
- 不使用“学长”等身份称谓，不展示密钥和个人敏感信息。

## XI. Technical Constraints Reminder

1. Every SVG root must include `width="1280"`, `height="720"`, and `viewBox="0 0 1280 720"`.
2. Background uses native `<rect>`.
3. Text wrapping uses `<tspan>`; no `<foreignObject>`.
4. No `rgba()`, `<style>`, `class`, `textPath`, animation, script, or group opacity.
5. Use only colors, fonts, and icons declared in `spec_lock.md`.
6. Top-level visual groups require stable `id` values.
7. XML reserved characters must be escaped.
