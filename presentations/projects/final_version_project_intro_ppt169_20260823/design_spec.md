# Design Specification & Content Outline

## I. Project Information

- **Project Title**: 成人肥胖中医诊前问诊系统
- **Presentation Type**: 最终版本项目介绍
- **Language**: 中文
- **Target Audience**: 项目组老师、同学，以及中医和医学信息化方向的评审者
- **Usage Occasion**: 课堂或组会项目汇报，约 8-10 分钟
- **Core Message**: 系统通过患者端对话式问诊、核心资料闭环判断和医生端结构化档案，为成人肥胖患者的诊中辨证、风险核查与检查准备提供可靠的诊前资料基础。
- **Content Strategy**: 严格按照用户确认的 10 页大纲，只介绍当前最终版本，不讲迭代变化。结构为用户自定，页序与标题保持不变。
- **Mode**: briefing。以完整、清晰、可扫描的方式介绍系统，不刻意制造结论先行或故事冲突。
- **Visual Style**: soft-rounded。使用克制圆角、轻量层次和充足留白，呈现成熟医疗产品的温和专业感。

## II. Canvas

- **Format**: PPT 16:9
- **ViewBox**: 0 0 1280 720
- **Safe Area**: x=56-1224, y=42-678
- **Grid**: 12 columns, 24 px gutters, 56 px outer margin
- **Page Number**: bottom-right, 14 px, secondary text

## III. Visual Theme

### Color Scheme

| Role | HEX | Usage |
| --- | --- | --- |
| Background | `#FCFDF9` | Main page field |
| Secondary background | `#F1F6EF` | Soft bands and grouped regions |
| Surface | `#FFFFFF` | Panels and screenshot placeholders |
| Primary | `#236B45` | Main titles, key nodes, strong emphasis |
| Accent | `#C68A3A` | Small highlights, sequence numbers, key thresholds |
| Secondary accent | `#72A984` | Supporting nodes and progress lines |
| Body text | `#24332B` | Main copy |
| Secondary text | `#68756D` | Notes and captions |
| Border | `#D7E2D8` | Dividers and panel outlines |
| Grid | `#E8EFE8` | Hairlines and placeholder guides |
| Alert | `#B44A45` | Safety and conflict signals only |

### Color Discipline

- Background and secondary background carry roughly 70% of each slide.
- Primary green carries 20-25%; warm gold is limited to 5-10%.
- No gradients. No more than four visible color families on one page.
- Alert red appears only on the safety/contradiction branch of Slide 07.

## IV. Typography

### Font Plan

- **Heading CJK / Latin**: `KaiTi, Georgia, serif`
- **Body CJK / Latin**: `"Microsoft YaHei", Arial, sans-serif`
- **Default fallback**: `"Microsoft YaHei", Arial, sans-serif`
- **Emphasis**: `KaiTi, Georgia, serif`
- **Code**: `Consolas, "Courier New", monospace`
- **Formula Policy**: text-only; this deck contains no formula-worthy expressions.

### Size Ramp

| Role | Size |
| --- | --- |
| Cover title | 68 px |
| Page title | 36 px |
| Large statement | 42-48 px |
| Subtitle | 26 px |
| Body baseline | 20 px |
| Caption / annotation | 14-16 px |
| Page number | 14 px |

## V. Layout System

- **Cover**: strong typographic composition with a large vertical clinical workflow motif; no centered title card.
- **Dense information pages**: use unframed columns, full-width bands, matrices, or one main panel plus support annotations.
- **Breathing pages**: one dominant assertion or decision path, with generous whitespace; avoid multi-card grids.
- **Screenshot pages**: one large 16:9 or browser-like placeholder with a thin dashed border, caption strip, and exact replacement instruction.
- **Corner radius**: 6-8 px only; no oversized pill cards.
- **Shadows**: none. Separation uses border, whitespace, and background contrast.
- **No nested cards**. Page sections remain unframed unless representing a real UI screenshot or repeated item.

## VI. Icon System

- **Library**: `tabler-filled`
- **Treatment**: one-color filled icons, normally primary green; reversed white only inside primary nodes.
- **Inventory**:
  - `tabler-filled/medical-cross`
  - `tabler-filled/flag`
  - `tabler-filled/message-chatbot`
  - `tabler-filled/clipboard-list`
  - `tabler-filled/shield-check`
  - `tabler-filled/user`
  - `tabler-filled/file-description`
  - `tabler-filled/search`
  - `tabler-filled/archive`
  - `tabler-filled/report-analytics`
  - `tabler-filled/database`
  - `tabler-filled/circle-check`

## VII. Visualization System

No quantitative data charts are required. The deck uses native SVG structural graphics:

| Page | Visualization | Construction | Reference |
| --- | --- | --- | --- |
| P03 | Three-problem chain | Three horizontally linked problem statements with one central outcome | no-template-match |
| P04 | System architecture flow | Patient side -> decision engine -> doctor side, with two supporting output rails | no-template-match |
| P05 | Four-step patient journey | Numbered horizontal path plus screenshot placeholder | no-template-match |
| P06 | Core information matrix | Four grouped bands mapping information domains | no-template-match |
| P07 | Completion decision path | Core-complete / conflict / optional-detail branches | no-template-match |
| P10 | Closed-loop summary | Four-node circular/linear loop and three value outcomes | no-template-match |

No chart-library templates are used because the content is process and system explanation rather than measured data.

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| patient_flow_screenshot.png | user supplied later | 16:9 preferred | Slide 05 system flow screenshot | Screenshot | #19 Image floating in whitespace with thin frame and caption + #70 Image with thin colored matte frame | placeholder | Placeholder | Current patient workflow page | | local |
| patient_interface_screenshot.png | user supplied later | 16:9 preferred | Slide 08 patient-side interface | Screenshot | #19 Image floating in whitespace with thin frame and caption + #70 Image with thin colored matte frame | placeholder | Placeholder | Current patient-side page | | local |
| doctor_interface_screenshot.png | user supplied later | 16:9 preferred | Slide 09 doctor-side archive and recommendations | Screenshot | #48 Side-by-side comparison + #70 Image with thin colored matte frame | placeholder | Placeholder | Current doctor-side page(s) | | local |

The SVG pages draw dashed placeholder frames and do not reference missing image files. The user will replace the placeholders in PowerPoint.

## IX. Content Outline

### Part 1: 项目定位

#### Slide 01 - 封面

- **Cover impact**: Use the phrase “把零散描述，整理成诊中可用资料” as the concrete hook. A large vertical sequence of four words — 收集 / 追问 / 整理 / 准备 — forms the visual spine on the right, while the project title anchors the left.
- **Layout**: High-contrast typographic poster with a primary-green field on the right third and an off-white title field on the left.
- **Title**: 成人肥胖中医诊前问诊系统
- **Subtitle**: 面向诊中决策的智能诊前资料整理
- **Info**: 项目介绍 · 最终版本

#### Slide 02 - 项目背景与定位

- **Layout**: Left statement + right role-boundary diagram.
- **Title**: 项目背景与定位
- **Core message**: 系统的职责不是诊断或开方，而是在诊前把成人肥胖患者的零散信息整理成医生可用的资料。
- **Content**:
  - 服务对象：成人肥胖患者与接诊医生。
  - 使用时点：患者就诊前完成信息收集，医生诊中继续确认。
  - 系统边界：不替代医生诊断，不直接生成处方，检查建议需要医生结合实际判断。

#### Slide 03 - 系统解决的问题

- **Layout**: Three linked horizontal issues leading to one outcome statement.
- **Title**: 系统解决的问题
- **Core message**: 项目把“说不清、问不全、看不快”转化为结构化、可追溯、可继续确认的诊前资料。
- **Content**:
  - 患者描述零散：症状、时间、诱因和既往情况常混在自然语言中。
  - 首次问诊时间有限：医生需要快速识别缺失信息和风险线索。
  - 中西医资料并存：既要保留中医症状，也要覆盖用药、过敏、既往史和代谢风险。
  - 最终输出：统一整理为诊前档案和检查准备建议。

### Part 2: 系统结构与使用流程

#### Slide 04 - 整体系统架构

- **Layout**: Three-stage architecture across the page with two output rails below.
- **Title**: 整体系统架构
- **Core message**: 患者端负责自然交互，后端负责规则与模型协同，医生端保留完整判断权。
- **Content**:
  - 患者端：基础资料、开放描述、对话追问、个人历史档案。
  - 后端：核心字段状态、问题优先级、冲突检查、模型生成与确定性规则。
  - 医生端：结构化档案、完整度明细、待确认信息、检查建议。
  - 技术实现：Vue 3 + Vite 前端，FastAPI 后端，大模型与规则引擎协同。

#### Slide 05 - 患者端使用流程

- **Layout**: Top four-step progress path; bottom large screenshot placeholder.
- **Title**: 患者端使用流程
- **Core message**: 患者从基础描述进入对话式追问，核心资料闭环后得到可回看的诊前档案。
- **Content**:
  - 1 基础信息与主要诉求
  - 2 开放式描述自身情况
  - 3 系统按信息缺口逐项追问
  - 4 生成诊前档案与检查建议
- **Screenshot placeholder**: “请放入当前患者端完整流程截图，建议使用浏览器 16:9 截图”。

#### Slide 06 - 核心信息采集内容

- **Layout**: Four horizontal information bands with one representative icon and grouped keywords each.
- **Title**: 核心信息采集内容
- **Core message**: 信息采集围绕肥胖病程、中医症状、安全用药和相关风险四个方面展开。
- **Content**:
  - 肥胖与病程：身高体重、腰围、体重变化、起病经过、诱因、既往减重经历。
  - 中医症状：食欲口渴、寒热汗出、二便、睡眠情绪、疲劳活动耐力、身体困重等。
  - 安全资料：过敏史、当前用药与保健品、危险信号、妊娠相关情况。
  - 相关风险：既往疾病、继发性肥胖线索、肝肾功能、代谢风险和近期检查。

#### Slide 07 - 追问何时结束：核心资料闭环

- **Layout**: One central readiness statement with a three-branch decision path below.
- **Title**: 追问何时结束：核心资料闭环
- **Core message**: 系统不以固定轮数结束，而以核心资料是否完成、是否存在冲突作为患者端停止条件。
- **Content**:
  - 可以结束：核心字段已形成可用答案，且关键回答之间没有未解决冲突。
  - 继续追问：仍缺少会影响诊中判断或用药安全的核心信息。
  - 转交医生：可选细节、不确定或拒答内容不无限追问，保留为医生诊中确认项。
  - 交互原则：一次只问一个重点；“不知道/拒答”最多友好澄清一次。

### Part 3: 两端体验与结果

#### Slide 08 - 患者端界面与交互

- **Layout**: Large screenshot placeholder on the right; left vertical annotation rail.
- **Title**: 患者端界面与交互
- **Core message**: 患者看到的是连续、可回看的对话体验，而不是内部完整度分数和缺失字段清单。
- **Content**:
  - 对话式追问，一次聚焦一个问题。
  - 回车发送，固定聊天区域内滚动查看全部历史。
  - 同一患者可以回看自己的历史问诊档案。
  - 内部完整度、必问缺失项和风险判定仅供医生端使用。
- **Screenshot placeholder**: “请放入当前患者端对话页面截图”。

#### Slide 09 - 医生端档案与检查建议

- **Layout**: Two large screenshot placeholders side by side with a narrow takeaway band below.
- **Title**: 医生端档案与检查建议
- **Core message**: 医生端将患者陈述、结构化字段和检查准备整合在同一份可继续确认的诊前档案中。
- **Content**:
  - 左侧占位：结构化诊前档案、完整问答记录、字段状态与待确认信息。
  - 右侧占位：根据已收集信息生成的推荐检查项目及注意事项。
  - 判断权：系统提供整理和提示，最终诊断、检查选择与处方由医生完成。
- **Screenshot placeholders**: “诊前档案/完整度明细”与“推荐检查项目”。

#### Slide 10 - 项目成果与应用价值

- **Closing impact**: The audience leaves with one clear idea: “把患者说过的话，变成医生接得住的资料。” Use a four-node closed loop as the visual anchor and three concise value outcomes at the bottom.
- **Layout**: Large central closed-loop workflow with a final statement across the lower third.
- **Title**: 项目成果与应用价值
- **Core message**: 当前系统已经形成从诊前信息收集到医生端使用的完整闭环。
- **Content**:
  - 完整流程：诊前收集 -> 对话追问 -> 档案整理 -> 检查准备。
  - 患者价值：降低表达负担，保留历史记录，减少重复描述。
  - 医生价值：提高首次就诊信息质量，快速发现缺口、冲突和风险线索。
  - 应用边界：服务诊中决策，不替代医生诊断和治疗。

## X. Speaker Notes Requirements

- Each page note matches its SVG filename.
- Notes use natural Chinese speaking language, 45-70 seconds per content page and 20-30 seconds for cover/closing.
- Every note includes one transition sentence into the next page.
- Do not mention iteration history, previous versions, or internal development feedback.

## XI. Technical Constraints

1. Every SVG root includes `width="1280" height="720" viewBox="0 0 1280 720"`.
2. Backgrounds use `<rect>` elements.
3. Text wrapping uses `<tspan>` only; `<foreignObject>` is forbidden.
4. Use `fill-opacity` / `stroke-opacity`; `rgba()` is forbidden.
5. Forbidden: `<style>`, `class`, `mask`, `textPath`, `<animate*>`, `<script>`, `<iframe>`, `@font-face`.
6. `<g opacity>` is forbidden; apply opacity to child elements.
7. All groups used for export have stable descriptive IDs.
8. Screenshot placeholders are native SVG rectangles and text, not missing image references.

