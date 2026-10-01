# AI 老中医结构化问诊项目周报 - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | AI 老中医结构化问诊项目周报 |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 10 |
| **Design Style** | briefing + soft-rounded |
| **Target Audience** | 导师、同事或项目负责人 |
| **Use Case** | 周工作汇报、项目阶段演示 |
| **Content Strategy** | balanced default；保留用户确认的 10 页顺序和标题，在每页内部提炼结论 |
| **Created Date** | 2026-07-29 |

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280x720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 56px，上 44px，下 38px |
| **Content Area** | 1168x638 |

## III. Visual Theme

### Theme Style

- **Mode**: briefing
- **Visual style**: soft-rounded
- **Theme**: 浅色主题
- **Tone**: 医疗产品、温和可信、清楚务实

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F7FAF7` | 页面背景 |
| **Secondary bg** | `#EEF6EF` | 区域底色、浅色面板 |
| **Primary** | `#2F7D4A` | 标题、主线、关键图形 |
| **Accent** | `#65B66C` | 重点状态、数字、进度 |
| **Secondary accent** | `#D9A441` | 少量中医文化强调 |
| **Body text** | `#1F2A24` | 正文 |
| **Secondary text** | `#5F6F64` | 说明、注释 |
| **Tertiary text** | `#8A978E` | 页脚、辅助信息 |
| **Border/divider** | `#D8E4DA` | 分隔线、卡片边框 |
| **Surface** | `#FFFFFF` | 主要内容容器 |
| **Grid** | `#E8F0E9` | 图表参考线、弱分隔 |
| **Success** | `#43A85B` | 测试通过、完成状态 |
| **Warning** | `#C74A45` | 风险与未完成事项 |

### Gradient Scheme

不使用装饰性渐变；仅在产品截图上用纯色半透明遮罩保证文字可读。

## IV. Typography System

### Font Plan

**Typography direction**: 清晰友好的中文无衬线字体，适合现场投屏。

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | Microsoft YaHei | Arial | sans-serif |
| **Body** | Microsoft YaHei | Arial | sans-serif |
| **Emphasis** | Microsoft YaHei | Arial | sans-serif |
| **Code** | - | Consolas, Courier New | monospace |

**Per-role font stacks**

- Title: `"Microsoft YaHei", Arial, sans-serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: same as Body
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 20px.

| Purpose | Size |
| ------- | ---- |
| Cover title | 64px |
| Page title | 36px |
| Hero number | 52px |
| Subtitle | 26px |
| Body content | 20px |
| Annotation / caption | 15px |
| Page number / footnote | 12px |

Formula policy: `text-only`。本项目汇报不包含公式。

## V. Layout Principles

### Page Structure

- **Header area**: 88px，标题、章节标签和页码。
- **Content area**: 544px，根据页面信息量使用非对称分栏、流程图或截图标注。
- **Footer area**: 30px，仅保留项目名和日期。

### Layout Pattern Library

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Negative-space-driven** | 封面、结论、单一重点 |
| **Asymmetric split** | 产品截图与改造成果说明 |
| **Three-column** | 本周工作概览、前端亮点 |
| **Top-bottom flow** | 问诊流程、数据流 |
| **Layered architecture** | 前后端职责和接口分层 |
| **KPI overview** | 测试与验证结果 |

### Spacing Specification

| Element | Current Project |
| ------- | --------------- |
| Safe margin from canvas edge | 56px |
| Content block gap | 28px |
| Icon-text gap | 12px |
| Card gap | 22px |
| Card padding | 24px |
| Card border radius | 12px |

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `tabler-outline`
- **Stroke width**: 2
- **Usage method**: `<use data-icon="tabler-outline/icon-name" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 项目与医疗 | `tabler-outline/report-medical` | P01 |
| 产品布局 | `tabler-outline/layout-dashboard` | P02, P04, P06 |
| 问诊流程 | `tabler-outline/route-square` | P05 |
| 后端服务 | `tabler-outline/server-cog` | P07 |
| 档案数据 | `tabler-outline/database-heart` | P08 |
| 浏览器验证 | `tabler-outline/browser-check` | P09 |
| 自动测试 | `tabler-outline/test-pipe` | P09 |
| 下一步目标 | `tabler-outline/target-arrow` | P10 |
| 信息确认 | `tabler-outline/clipboard-check` | P05 |
| 隐私与可靠性 | `tabler-outline/shield-check` | P06, P08 |
| 设计思路 | `tabler-outline/bulb` | P03 |

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim from `charts_index.json`) | Usage |
| ---- | -------- | ---- | ------------------------------------------------- | ----- |
| P02 | icon_grid | `templates/charts/icon_grid.svg` | "Pick for 4-9 parallel features/capabilities/services as icon cards 鈥?feature grid, service lineup, benefits matrix, brand values, product highlights. Skip for sequential ordering (use numbered_steps) or hierarchical layers (use pyramid_chart)." | 四项本周成果概览 |
| P03 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description 鈥?design principles, core tenets, action items, key takeaways, recommendations, executive summary points. Skip for icon-style cards (use icon_grid) or sequential steps (use numbered_steps)." | 三项改版前问题 |
| P05 | process_flow | `templates/charts/process_flow.svg` | "Pick for 3-8 sequential steps connected by simple arrows 鈥?approval workflows, customer onboarding, request handling, lifecycle stages. Skip if cyclical (use circular_stages) or stages produce named outputs (use pipeline_with_stages)." | 四阶段问诊流程 |
| P07 | layered_architecture | `templates/charts/layered_architecture.svg` | "Pick for 3-4 horizontal architecture layers (presentation/service/data), 2-4 module cards per layer, each card = title + 1-line description (description required, even if source brief). Skip if no per-module descriptions (use icon_grid) or no horizontal layering (use module_composition)." | 前端、流程服务、Agent 与数据层 |
| P08 | pipeline_with_stages | `templates/charts/pipeline_with_stages.svg` | "Pick for 3-5 horizontal pipeline stages, each = title + 1-line description + output artifact, connected by arrows (data pipelines, ETL, build pipelines). Skip if any stage lacks an artifact (use process_flow or numbered_steps)." | 答案到档案的数据沉淀 |
| P09 | kpi_cards | `templates/charts/kpi_cards.svg` | "Pick for 4-8 standalone numeric metrics shown as overview cards (2x2 or 1x4) 鈥?exec summary opener, dashboard headline, quarterly recap, results-at-a-glance. Skip if metrics have target baselines (use bullet_chart) or single hero number (use gauge_chart)." | 测试、构建与浏览器验证 |
| P10 | numbered_steps | `templates/charts/numbered_steps.svg` | "Pick for 3-6 horizontal sequential steps with numeric emphasis 鈥?how-it-works section, getting-started guide, methodology overview, implementation phases. Skip if steps need connector arrows (use process_flow) or named output artifacts (use pipeline_with_stages)." | 下一阶段四项计划 |

**Runners-up considered**

- `roadmap_vertical` | rejected for P10：下一步尚未绑定明确日期，按步骤表达更准确。
- `labeled_card` | rejected for P02：四项成果需要图标识别和快速扫描，icon_grid 更合适。
- `module_composition` | rejected for P07：后端内容存在清楚的层级关系，layered_architecture 更贴合。

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | ---------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| current-ui.png | 1265x1304 | 0.97 | P04 展示产品整体形态，P06 标注前端关键区域 | Product screenshot | `#4 Right image bleeding off the canvas edge + #21 Rounded rectangle crop + #70 Image with thin colored matte frame`; P06 使用 `#45 Background image + numbered hotspots with sidebar legend + #46 Background image + bordered "lens" rectangle highlighting a sub-region` | user | Existing | 当前中医智能助手三栏结构化问诊界面 | | |

## IX. Content Outline

### Part 1: 项目与成果

#### Slide 01 - 封面

- **Cover impact**: 用“从聊天窗口到结构化问诊产品”作为改造成果钩子，配合左侧大标题和右侧抽象问诊路径，形成明确的升级方向。
- **Layout**: 负空间主导；左侧标题，右侧用原生 SVG 绘制 4 个流程节点。
- **Title**: AI 老中医问诊系统
- **Subtitle**: 本周工作汇报｜结构化问诊产品升级
- **Info**: 2026.07.30

#### Slide 02 - 本周工作概览

- **Layout**: 2x2 图标矩阵，顶部结论标题。
- **Title**: 本周完成了一次产品化升级
- **Core message**: 工作重点不是单纯换皮，而是同时改造了交互流程、前端界面、后端状态和数据保存。
- **Visualization**: icon_grid
- **Content**:
  - 产品形态：聊天式问诊升级为引导式预问诊
  - 前端体验：三栏布局、进度、题目状态和信息摘要
  - 后端能力：10 题状态流程与完整接口
  - 工程质量：自动测试、构建和浏览器流程验证

#### Slide 03 - 改版前的问题

- **Layout**: 左侧大号“3”，右侧纵向三项问题。
- **Title**: 旧版能对话，但还不像一个完整产品
- **Core message**: 自由聊天缺少稳定流程、可见进度和结构化数据，限制了演示效果与后续扩展。
- **Visualization**: vertical_list
- **Content**:
  - 用户表达成本高：需要自己组织症状，容易遗漏
  - 问诊过程不透明：不知道问到哪里、还剩多少
  - 数据难沉淀：回答偏自然语言，后续档案利用困难

### Part 2: 产品与技术改造

#### Slide 04 - 产品形态升级

- **Layout**: 左侧“旧版 → 新版”对照结论，右侧使用当前产品截图。
- **Title**: 从聊天演示升级为结构化问诊工作台
- **Core message**: 新版把问诊变成可看、可选、可回退、可完成的连续任务。
- **Content**:
  - 旧版：单一聊天窗口，主要依赖用户输入
  - 新版：流程导航 + 当前问题 + 进度摘要
  - 用户不打字也能完成问诊，同时保留补充描述

#### Slide 05 - 问诊流程设计

- **Layout**: 横向四阶段流程，底部补充 10 个核心问题范围。
- **Title**: 固定主流程保证完整，AI 保留温度与弹性
- **Core message**: 问诊顺序由结构化流程控制，AI 负责解释、追问和最终整理。
- **Visualization**: process_flow
- **Content**:
  - 导诊：了解主要症状
  - 预问诊：完成中医十问歌核心信息
  - 信息确认：回看并修正已收集内容
  - 检查建议：生成保守建议与四诊档案
  - 10 题覆盖主诉、病程、寒热、汗、头身、二便、饮食、胸腹、睡眠、病史诱因

#### Slide 06 - 前端改造亮点

- **Layout**: 产品截图作为主画面，四个原生 SVG 热点标出关键区域，右侧小型图例。
- **Title**: 用户始终知道“现在在哪、还差什么”
- **Core message**: 三栏界面把流程、当前操作和信息反馈同时呈现，降低了问诊的不确定感。
- **Content**:
  - 左侧：四阶段问诊导航
  - 中间：题目、选项、补充描述和前后切换
  - 右侧：进度、题目状态和已收集信息
  - 响应式布局：桌面三栏，小屏自动转为可用单栏

#### Slide 07 - 后端能力建设

- **Layout**: 四层横向架构图，每层 2-4 个模块。
- **Title**: 后端新增一层可持续推进的问诊状态机
- **Core message**: 后端从一次性聊天接口扩展为可读取、提交、回退、完成的会话流程。
- **Visualization**: layered_architecture
- **Content**:
  - 展示层：Vue 页面、问题选择、进度同步
  - 流程层：会话状态、当前题号、答案更新、回退
  - 智能层：Qwen / Ollama、解释、追问、档案整理
  - 数据层：结构化答案、Markdown 报告、JSON 记录
  - 新增接口：GET state、POST answer、POST move、POST complete

#### Slide 08 - 四诊档案与数据沉淀

- **Layout**: 四阶段数据管线，右侧展示最终档案字段。
- **Title**: 每一次回答都能转化为可复用的结构化档案
- **Core message**: 新增 structured_answers 后，问诊数据既保留用户原话，也能支持后续分析和档案管理。
- **Visualization**: pipeline_with_stages
- **Content**:
  - 用户选择与补充描述
  - 后端更新会话和摘要
  - 完成后生成四诊档案 Markdown
  - 保存为包含 structured_answers 的 JSON 记录
  - 数据价值：可检索、可回看、可继续扩展专病分支

### Part 3: 验证与下一步

#### Slide 09 - 测试与验证

- **Layout**: 2x2 KPI 卡片，底部一行结论。
- **Title**: 核心流程已经通过代码和浏览器双重验证
- **Core message**: 当前版本完成了后端单元测试、语法检查、前端构建和真实交互验证。
- **Visualization**: kpi_cards
- **Content**:
  - 4 / 4：后端单元测试通过
  - 0：Python 语法错误
  - 86：前端成功构建模块数
  - 1 条完整路径：选择答案 → 下一题 → 进度与摘要同步
  - 结论：核心演示链路可用，服务停止时需重新启动前后端

#### Slide 10 - 下一步计划

- **Closing impact**: 让听众记住“当前已经是可演示产品，下一步要走向更智能、更完整、更稳定”，用四步路线和一句结论收束。
- **Layout**: 横向四步路线，底部使用主色结论条。
- **Title**: 下一阶段：从可用走向更智能、更完整
- **Core message**: 下一步优先补强 AI 动态追问、异常风险提示、档案管理和部署稳定性。
- **Visualization**: numbered_steps
- **Content**:
  - 1. 根据结构化答案生成动态追问
  - 2. 增加风险信号与就医提醒
  - 3. 完善档案列表、搜索和详情页
  - 4. 优化启动方式、部署与演示稳定性
  - 收束：本周已经完成从聊天 Demo 到结构化问诊产品的关键一步

## X. Speaker Notes Requirements

- **Total duration**: 8-10 分钟
- **Style**: 自然、务实，技术细节用非专业语言解释
- **Purpose**: 汇报本周成果，展示产品价值和下一步方向
- **Filename**: 与 SVG 文件名一致
- **Content**: 每页包含开场句、2-4 个讲述要点、过渡句和建议用时

## XI. Technical Constraints Reminder

### SVG Generation Must Follow

1. viewBox: `0 0 1280 720`
2. 背景使用 `<rect>`
3. 文本换行使用 `<tspan>`
4. 透明度使用 `fill-opacity` / `stroke-opacity`
5. 禁止 `<style>`、`class`、`foreignObject`、`textPath`、`animate*`、`script`
6. 禁止 `<g opacity>`
7. XML 保留字符必须转义
8. `clipPath` 只用于 `<image>`

### PPT Compatibility Rules

- 所有文字保持可编辑
- 产品截图使用 `no-crop`
- 每页顶层元素使用有意义的 `<g id="...">`
- 图标只使用已同步的 `tabler-outline` 库
