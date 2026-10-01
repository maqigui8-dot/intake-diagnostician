# Design Specification & Content Outline

## I. Project Information

- **Project**: 中医诊前问诊系统阶段改进
- **Purpose**: 汇报原版本问题、主要改进和当前完整使用流程
- **Audience**: 项目组成员、指导教师及阶段汇报听众
- **Usage**: 现场中文进展汇报，预计 7–9 分钟
- **Language**: 简体中文
- **Page Count**: 7 pages
- **Content Strategy**: 用户确认的 7 页结构为权威顺序；内容紧贴项目真实页面和现有实现，不引入外部事实
- **Mode**: briefing — 以清晰、完整、可扫描的方式说明产品改进与当前流程
- **Visual Style**: soft-rounded — 延续项目本身的医疗产品界面，轻圆角、浅色分区、克制留白

## II. Canvas

- **Format**: PPT 16:9
- **Dimensions**: 1280 × 720
- **ViewBox**: `0 0 1280 720`
- **Safe Margin**: 48px horizontal, 40px vertical

## III. Visual Theme

### Color Scheme

- Background: `#FFFFFF`
- Surface: `#F5F8F4`
- Primary: `#2F8F4E`
- Primary Dark: `#1D5732`
- Primary Light: `#E6F4E8`
- Problem: `#D95D4F`
- Problem Light: `#FCEDEA`
- Accent: `#D6A74B`
- Accent Light: `#FBF4DF`
- Body Text: `#21352A`
- Secondary Text: `#6C7A70`
- Border: `#DCE5DD`
- Muted: `#A5B0A8`

Color behavior: white and pale green carry most of each page; green represents the improved experience and active flow, red marks old problems, and gold marks decision points or supporting mechanisms.

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
- Cover title: 60px
- Page title: 36px
- Subtitle: 27px
- Mid-level heading: 24px
- Annotation: 14px
- Footer: 12px

Formula rendering policy: text-only; no formula assets are required.

## V. Layout Principles

- Header area: x=48, y=42–108；英文小标签 + 中文页面标题。
- Content area: y=132–654；截图页优先使用左侧 300–330px 讲解区和右侧 810–840px 截图区。
- Footer area: y=686；项目名称与页码。
- Screenshot containers: 12px rounded corners, 1–2px border, no crop, no distortion.
- Dense pages use two-column explanations or process lanes；P03 is a screenshot-led breathing page.
- Avoid nested cards and marketing-style hero copy; screenshots remain the evidence and visual focus.

## VI. Icon Usage Specification

- **Library**: `tabler-outline`
- **Stroke width**: `2`
- **Inventory**: `alert-circle`, `refresh`, `eye-off`, `message-circle`, `list-check`, `route`, `file-text`, `stethoscope`, `shield-check`, `brain`, `repeat`, `checks`, `clipboard-list`, `notes`, `arrow-right`, `user-question`

| Purpose | Icon Path | Page |
| --- | --- | --- |
| 原版问题 | `tabler-outline/alert-circle` | P02 |
| 页面刷新 | `tabler-outline/refresh` | P02 |
| 隐藏内部字段 | `tabler-outline/eye-off` | P02, P03 |
| 对话式追问 | `tabler-outline/message-circle` | P03, P06 |
| 基础必问项 | `tabler-outline/list-check` | P04, P05 |
| 完整流程 | `tabler-outline/route` | P04 |
| 诊前档案 | `tabler-outline/file-text` | P04, P07 |
| 检查建议 | `tabler-outline/stethoscope` | P04, P07 |
| 收敛保护 | `tabler-outline/shield-check` | P06 |
| 问法 Skill | `tabler-outline/brain` | P06 |
| 动态重分析 | `tabler-outline/repeat` | P06 |
| 完成状态 | `tabler-outline/checks` | P03, P07 |

## VII. Visualization Reference List

No catalog chart template is required. P04 uses a custom native SVG process flow. P02 uses a custom four-problem diagnostic layout. All other pages are screenshot-led explanatory layouts.

Runners-up considered:

- `timeline_horizontal` — rejected because the process contains an analysis-and-follow-up loop rather than a one-way timeline.
- `process_flow_steps` — rejected because the page needs five named product stages and a conditional loop-back.
- `comparison_matrix` — rejected because P02 is a problem diagnosis, not a two-axis comparison.

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_dialogue_current.png | 1906×920 | 2.07 | P03 主要改进后的对话页面 | UI Screenshot | #3 Right-third image + left text body + #21 Rounded rectangle crop + #70 Image with thin colored matte frame | user | Existing | 当前对话式追问实机页面 | | local |
| 02_base_ten_questions.png | 1891×921 | 2.05 | P05 十个基础必问项页面 | UI Screenshot | #3 Right-third image + left text body + #21 Rounded rectangle crop + #70 Image with thin colored matte frame | user | Existing | 基础问题 1/10 实机页面 | | local |
| 03_follow_up_chat.png | 1888×904 | 2.09 | P06 对话式追问阶段页面 | UI Screenshot | #3 Right-third image + left text body + #21 Rounded rectangle crop + #70 Image with thin colored matte frame | user | Existing | 第 7 问对话式追问实机页面 | | local |
| 04_final_record.png | 1896×923 | 2.05 | P07 完整诊前档案 | UI Screenshot | #53 Vertical image stack + #21 Rounded rectangle crop + #70 Image with thin colored matte frame | user | Existing | 诊前档案表格实机页面 | | local |
| 05_exam_recommendations.png | 1594×193 | 8.26 | P07 推荐检查项目 | UI Screenshot | #53 Vertical image stack + #21 Rounded rectangle crop + #70 Image with thin colored matte frame | user | Existing | 检查建议实机页面 | | local |

## IX. Content Outline

### Part 1: 问题与改进

#### Slide 01 - 中医诊前问诊系统阶段改进

- **Cover impact**: 用“问题卡 → 连续对话 → 完整档案”的三段式转化作为视觉钩子，标题位于左侧，右侧使用原生 SVG 抽象流程。
- **Layout**: 负空间主导的封面，左侧大标题，右侧三阶段形态。
- **Title**: 中医诊前问诊系统
- **Subtitle**: 问题改进与当前完整使用流程
- **Info**: 阶段进展汇报 · 2026.08.13

#### Slide 02 - 原来存在的问题

- **Layout**: 四个问题块围绕一个“用户体验中断”中心结论，使用红色问题标记。
- **Title**: 原来存在的问题
- **Core message**: 原版本的追问体验不连续，并向患者展示了不必要的内部判断。
- **Content**:
  - 追问不是连续聊天式，历史上下文不突出。
  - 回答后需要刷新或重新进入，才能看到后续问题。
  - 信息完整度、缺失必问项、建议选问项等内部字段直接展示给用户。
  - 页面信息较多，患者当前任务不够集中。

#### Slide 03 - 主要改进

- **Layout**: 左侧四项改进，右侧大幅显示 `01_dialogue_current.png`。
- **Title**: 主要改进：从单题卡片到连续对话
- **Core message**: 追问被改造成无需刷新、保留历史、仅展示必要内容的连续聊天体验。
- **Content**:
  - 独立的对话式追问页面。
  - 历史问题和回答持续可见。
  - 回答提交后自动整理并进入下一问，无需刷新。
  - 删除或隐藏完整度、缺失必问项、建议选问项等患者不需要看到的内容。

### Part 2: 当前完整流程

#### Slide 04 - 当前完整使用流程

- **Layout**: 五阶段水平主线，第三阶段包含“重新分析”的回环箭头。
- **Title**: 当前完整使用流程
- **Core message**: 从基础采集到诊前档案和检查建议的完整业务闭环。
- **Content**:
  - ① 10 个基础必问项。
  - ② 完整度判断。
  - ③ 对话式追问，一轮一问并持续重分析。
  - ④ 生成完整诊前档案。
  - ⑤ 生成推荐检查项目。

#### Slide 05 - 第一阶段：完成 10 个基础必问项

- **Layout**: 左侧说明标准化基础采集和 Skill 作用，右侧显示 `02_base_ten_questions.png`。
- **Title**: 第一阶段：完成 10 个基础必问项
- **Core message**: 先通过标准化问题建立完整度判断所需的基础资料。
- **Content**:
  - 主诉、持续时间、寒热、汗出、头身、二便、饮食、胸腹、睡眠、旧病与诱因等基础维度。
  - `tcm-intake-checklist` 根据十问歌、主诉和问诊经验区分基础必问项与条件选问项。
  - 完成固定十题不等于资料一定完整，后续仍由系统判断是否需要补问。

#### Slide 06 - 第二阶段：进入对话式追问

- **Layout**: 左侧说明一轮一问和收敛规则，右侧显示 `03_follow_up_chat.png`，底部使用四项策略带。
- **Title**: 第二阶段：进入对话式追问
- **Core message**: 系统每轮只补齐一个关键缺口，并通过稳定 key 和安全策略保证追问能够结束。
- **Content**:
  - `tcm-questioning-guide` 将最重要的缺口转成自然、温和、单一问点的问题。
  - 历史问答持续显示，提交后自动进入下一轮，无需刷新。
  - 同一缺口使用稳定 key，已经询问后不得换一种问法重复。
  - 选问项不能阻止结束；后台设置 12 轮安全保护。

#### Slide 07 - 最终输出：诊前档案与检查建议

- **Closing impact**: 用上下堆叠的真实结果页面说明“采集的信息最终变成什么”，左侧用两句结论收束。
- **Layout**: 左侧结果说明，右侧上方显示 `04_final_record.png`，下方显示 `05_exam_recommendations.png`。
- **Title**: 最终输出：诊前档案与检查建议
- **Core message**: 问诊结束后，系统将全部基础回答和补充追问整理为可供后续诊中参考的结构化资料。
- **Content**:
  - 完整诊前档案汇总四诊相关信息和全部补充问答。
  - 推荐检查项目与当前主诉和已知风险相关，并提供检查方式、科室、临床意义和注意事项。
  - 结果仅用于诊前信息整理，不能替代医生诊断和检查决策。

## X. Speaker Notes Requirements

- 讲述顺序固定为：原来有什么问题 → 今天改了什么 → 现在用户如何完成全过程 → 最终得到什么。
- 每页 40–70 秒，P04 流程页约 80 秒。
- 不在正文展开 API、代码文件和接口字段；Skill 只解释业务职责。
- 不出现“学长”等称谓，不展示 API Key 或其他敏感信息。
- 外部来源为零；5 张截图均为用户提供的项目实机页面。

## XI. Technical Constraints Reminder

1. Every SVG root includes `width="1280"`, `height="720"`, and `viewBox="0 0 1280 720"`.
2. Background uses native `<rect>` elements.
3. Text wrapping uses `<tspan>`; `<foreignObject>` is forbidden.
4. Use `fill-opacity` and `stroke-opacity`; `rgba()` is forbidden.
5. Forbidden: `<style>`, `class`, `textPath`, animation, script, iframe, group opacity.
6. Screenshots use only files listed in `spec_lock.md`, with `preserveAspectRatio="xMidYMid meet"`.
7. Use only colors, fonts, and icons declared in `spec_lock.md`.
8. XML reserved characters must be escaped.
