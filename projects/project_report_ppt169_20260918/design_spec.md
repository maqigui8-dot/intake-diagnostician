# Design Specification & Content Outline

## I. Project Information

- **Project**: 中医诊前信息采集与整理系统项目汇报
- **Purpose**: 组会汇报项目背景、实现方案、核心机制、关键难点与操作效果
- **Audience**: 课题组老师和组会成员
- **Language**: 简体中文
- **Page count**: 14页
- **Content strategy**: 严格沿用用户确认的14页顺序；每页内容适度丰富，便于现场讲解，不改变重点。
- **Structure authority**: 用户确认的大纲为页面顺序与标题的权威来源。
- **Core message**: 该项目以规则系统约束Agent，将患者自由描述转化为可追踪、可解释的诊前资料。

## II. Canvas Format

- **Format**: PPT 16:9
- **Canvas**: 1280 × 720
- **ViewBox**: `0 0 1280 720`
- **Safe margin**: 左右68px，上52px，下44px

## III. Visual Theme

- **Mode**: `briefing`。按项目背景、系统设计、核心机制、难点和操作展示依次说明，标题使用中性主题式表达。
- **Visual style**: `swiss-minimal`。延续参考PPT的大面积留白、细分隔线、无阴影、强字重标题和严格对齐。
- **Reference identity**: 暖米白底、深墨绿标题、陶土橙短线、灰绿色正文；不使用蓝紫色。
- **Background**: `#F7F5EF`
- **Secondary background**: `#EFEEE8`
- **Primary / heading**: `#155348`
- **Accent**: `#C86A3A`
- **Secondary accent / dividers**: `#BFCFC9`
- **Body text**: `#566762`
- **Strong text**: `#263D38`
- **Muted text**: `#7B8783`
- **Border / grid**: `#D7DEDA`
- **Color behavior**: 背景占绝大多数；深墨绿负责标题和关键结构；陶土橙只用于短横线、编号或单个强调点；每页不超过四种颜色。
- **Texture and elevation**: 严格扁平，无渐变、无阴影、无拟物。

## IV. Typography

- **Direction**: 与参考PPT一致的现代中文无衬线；依靠字号和字重建立层级。

| Role | Chinese | English | Fallback tail |
|---|---|---|---|
| Title | Microsoft YaHei | Arial | sans-serif |
| Body | Microsoft YaHei | Arial | sans-serif |
| Emphasis | Microsoft YaHei | Arial | sans-serif |
| Code | — | Consolas | monospace |

- **Title stack**: `"Microsoft YaHei", Arial, sans-serif`
- **Body stack**: `"Microsoft YaHei", Arial, sans-serif`
- **Emphasis stack**: `"Microsoft YaHei", Arial, sans-serif`
- **Code stack**: `Consolas, "Courier New", monospace`
- **Body baseline**: 20px
- **Cover title**: 58px，700–800字重
- **Page title**: 34px，700字重，统一左上角
- **Subtitle / lead**: 26px
- **Body**: 20px
- **Caption / annotation**: 15px
- **Page number**: 12px
- **Formula policy**: text-only；本项目无复杂公式。

## V. Layout Principles

- **Header area**: 标题从x=68、y=54开始；标题下使用一条48–72px陶土橙短线。封面参考原PPT居中处理。
- **Content area**: y=138–650；按信息重量选择分栏、流程或裸文本，不统一套卡片。
- **Footer area**: 页码位于右下角；必要时加一条浅灰绿细线。
- **Universal gap**: 28–36px；栏目间距36–48px；同组文字间距12–18px。
- **Shape language**: 直角矩形、真圆、单线宽分隔；圆角原则上0–4px。
- **Text density**: 每页4–6个内容点；单条尽量控制在两行内；机制页可以配一句解释性结论。
- **Title rule**: 除封面外，所有页面标题均靠左上角。
- **Image placeholders**: P12–P14使用米白背景上的细边框截图占位框，标注截图名称；不生成虚假产品截图。

## VI. Icon Usage Specification

- **Approach**: 默认不使用图标。流程、架构和优先级通过线条、箭头、编号、圆点和文字完成。
- **Reason**: 保持与参考PPT一致，避免图标堆砌和明显AI模板感。

## VII. Visualization Reference List

| Page | Template | Path | Summary-quote | Usage |
|---|---|---|---|---|
| P04 | layered_architecture | `templates/charts/layered_architecture.svg` | "Pick for 3-4 horizontal architecture layers (presentation/service/data), 2-4 module cards per layer, each card = title + 1-line description (description required, even if source brief). Skip if no per-module descriptions (use icon_grid) or no horizontal layering (use module_composition)." | 展示患者端、服务层、规则与Agent、数据层的系统架构 |
| P06 | process_flow | `templates/charts/process_flow.svg` | "Pick for 3-8 sequential steps connected by simple arrows — approval workflows, customer onboarding, request handling, lifecycle stages. Skip if cyclical (use circular_stages) or stages produce named outputs (use pipeline_with_stages)." | 展示患者问诊的完整流程 |
| P09 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendations, executive summary points. Skip for icon-style cards (use icon_grid) or sequential steps (use numbered_steps)." | 展示下一问的五级追问优先级 |
| P10 | process_flow | `templates/charts/process_flow.svg` | "Pick for 3-8 sequential steps connected by simple arrows — approval workflows, customer onboarding, request handling, lifecycle stages. Skip if cyclical (use circular_stages) or stages produce named outputs (use pipeline_with_stages)." | 展示继续追问与停止追问的判断路径 |

**Runners-up considered**:

- `pipeline_with_stages`：P06没有每一步独立产物，不采用。
- `pyramid_chart`：P09是顺序优先级而非层级成熟度，不采用。
- `chevron_process`：P10存在条件分支，不适合粗重箭头链，不采用。

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
|---|---:|---:|---|---|---|---|---|---|---|---|
| patient-entry-placeholder | — | 1.78 | P12身份选择与患者端截图位置 | Screenshot placeholder | #50 Tiled grid (2×2, 2×3, 3×3) with equal cells + #70 Image with thin colored matte frame | placeholder | Placeholder | 用户后续替换为实际截图 | | local |
| intake-flow-placeholder | — | 1.78 | P13开放描述、补充追问与档案截图位置 | Screenshot placeholder | #47 Small multiples — 3–6 same-kind images in an evenly spaced row + #70 Image with thin colored matte frame | placeholder | Placeholder | 用户后续替换为实际截图 | | local |
| doctor-workspace-placeholder | — | 1.78 | P14医生三栏工作台截图位置 | Screenshot placeholder | #19 Image floating in whitespace with thin frame and caption + #70 Image with thin colored matte frame | placeholder | Placeholder | 用户后续替换为实际截图 | | local |

> `previous-style-reference.png`仅作为视觉参考，不进入最终页面。

## IX. Content Outline

### Part 1：项目背景与总体设计

#### Slide 01 - 封面

- **Cover impact**: 以参考PPT的克制留白作为主视觉，主标题居中偏上，陶土橙短横线形成唯一强调；下方只保留汇报人和日期，不加副标题。
- **Layout**: 暖米白满版背景；标题居中；底部细线与页码。
- **Title**: 中医诊前信息采集与整理系统
- **Info**: 汇报人、日期占位

#### Slide 02 - 项目背景与问题

- **Layout**: 左侧问题引入，右侧四项问题按编号纵向排列，底部放一句项目需求总结。
- **Title**: 项目背景与问题
- **Core message**: 说明诊前信息采集存在描述零散、重复问询、停止条件不清和决策不可解释的问题。
- **Content**:
  - 患者往往不知道从哪里说起，表达自然但信息零散。
  - 医生需要重复询问基础资料、病程、生活方式与安全信息。
  - 普通聊天式问诊容易持续追问，可选细节也会阻塞结束。
  - 医生难以理解系统为什么选择当前问题、为什么此时停止。
  - 项目需求：结构化采集、有限追问、及时停止、过程可解释。

#### Slide 03 - 项目目标与定位

- **Layout**: 上半部分“项目目标”四项，下半部分“能力边界”四项，用细线分区而非卡片。
- **Title**: 项目目标与定位
- **Core message**: 说明项目用于诊前资料整理，而不是替代医生诊断。
- **Content**:
  - 将患者自然语言整理为结构化诊前资料。
  - 根据缺失信息选择下一项追问，并控制重复询问。
  - 根据核心信息完整度判断何时停止。
  - 为医生提供可追踪、可解释的问诊结果。
  - 不自动诊断、不输出患病概率、不自动开方、不替代面诊。

#### Slide 04 - 系统整体架构

- **Layout**: 四层横向架构，左侧标层级，右侧放模块与一句说明。
- **Title**: 系统整体架构
- **Core message**: 展示患者端、FastAPI服务、规则与Agent、MySQL数据层之间的职责关系。
- **Visualization**: `layered_architecture`
- **Content**:
  - 交互层：Vue 3患者端与独立医生工作台。
  - 接口层：FastAPI提供患者隔离接口和医生只读接口。
  - 决策层：Agent信息抽取、字段状态、完整度、下一问和停止判断。
  - 数据层：MySQL保存患者、会话、字段、问答、档案与审计记录。
  - 设计原则：大模型负责理解与表达，规则系统负责决策与约束。

#### Slide 05 - 系统角色与主要功能

- **Layout**: 左右双栏；患者端与医生端等高并列，中间用细线分隔。
- **Title**: 系统角色与主要功能
- **Core message**: 区分患者提供信息与医生查看理解信息的职责。
- **Content**:
  - 患者端：身份选择、基础资料、开放描述、逐项追问、未完成问诊恢复、历史档案。
  - 医生端：患者切换、历次问诊、基础资料、问答记录、完整度、缺口、追问来源、停止原因。
  - 数据边界：每个会话和档案显式绑定`patient_id`。
  - 医生端第一版保持只读，不修改患者原始回答。

### Part 2：问诊机制与可解释决策

#### Slide 06 - 完整问诊流程

- **Layout**: 七步水平流程，上方为阶段名称，下方为一句解释；底部突出“每次回答后重新判断”。
- **Title**: 完整问诊流程
- **Core message**: 展示从患者身份选择到医生查看档案的完整数据流。
- **Visualization**: `process_flow`
- **Content**: 选择患者 → 基础资料 → 开放描述 → Agent提取 → 字段更新 → 完整度判断 → 追问或生成档案 → 医生查看。

#### Slide 07 - 结构化字段与信息来源

- **Layout**: 五列字段类别；下方横向说明字段定义内容与来源。
- **Title**: 结构化字段与信息来源
- **Core message**: 说明系统采集的字段范围以及字段为什么能够参与规则决策。
- **Content**:
  - 基础测量：年龄、性别、身高、体重、腰围等。
  - 病程信息：体重变化、起病经过、相关因素、既往管理经历。
  - 中医症状：食欲口渴、二便、睡眠情绪、疲劳等。
  - 生活方式：饮食、运动、作息、压力性进食。
  - 安全信息：过敏、用药、重要病史、妊娠、危险信号。
  - 每个字段包含优先级、核心属性、最大尝试次数、标准问题和信息来源。

#### Slide 08 - 资料完整度如何判断

- **Layout**: 左侧字段状态阶梯，右侧判断清单，底部用一句话总结完整度原则。
- **Title**: 资料完整度如何判断
- **Core message**: 完整度由核心字段、安全缺口与冲突共同决定，而不是要求所有可选字段全部完成。
- **Content**:
  - 字段状态：尚未询问、部分获取、已确认、无法提供、不适用。
  - 首先确认基础测量是否完成。
  - 检查核心病程和安全字段是否仍有缺口。
  - 存在未解决冲突时，相关字段继续作为阻塞项。
  - 可选字段不会无限阻塞患者端结束。
  - 每次回答后重新计算完整度，并输出完成数与关键缺口。

#### Slide 09 - 追问优先级与决策机制

- **Layout**: 五级纵向编号列表，右侧增加“用药与运动同时缺失”的具体例子。
- **Title**: 追问优先级与决策机制
- **Core message**: 下一问由确定性优先级选择，Agent只负责把目标字段表达成自然问题。
- **Visualization**: `vertical_list`
- **Content**:
  - 第一优先：危险信号与安全字段。
  - 第二优先：尚未完成的核心字段。
  - 第三优先：存在冲突、需要澄清的字段。
  - 第四优先：高优先级普通字段。
  - 第五优先：可选补充信息。
  - 已确认、不适用或达到最大尝试次数的字段不再重复询问。

#### Slide 10 - 何时停止追问

- **Layout**: 中央判断节点，左侧“继续追问”，右侧“停止追问”；停止分正常结束和保护性结束。
- **Title**: 何时停止追问
- **Core message**: 系统不依赖固定轮数，而是根据核心信息完整度和在线可采集性停止。
- **Visualization**: `process_flow`
- **Content**:
  - 正常结束：核心字段完整、无关键安全缺口、无未解决冲突。
  - 保护性结束：患者多次无法回答、剩余内容不适合在线采集、问题重复、AI暂不可用。
  - 危险信号：持续提示安全风险，并建议优先就医。
  - 保护性结束不代表资料完整，而是保存当前结果交由医生补充。

#### Slide 11 - 项目实现中的关键难点

- **Layout**: 四个横向编号模块，每个包含“问题—解决方式—当前状态”。
- **Title**: 项目实现中的关键难点
- **Core message**: 总结追问轮数、模型不确定性、重复回答和多患者隔离四项难点及实现状态。
- **Content**:
  - 追问轮数过多：从全部字段完成改为核心字段驱动停止；已实现。
  - Agent输出不稳定：Agent提供证据，确定性规则负责决策；已实现。
  - “不知道”导致重复：记录尝试次数与回答质量，达到上限转医生补充；已实现。
  - 多患者数据隔离：显式`patient_id`、资源归属校验、跨患者访问返回404；已实现。
  - 当前边界：演示身份不等于正式鉴权，真实临床效果仍需进一步验证。

### Part 3：项目操作展示

#### Slide 12 - 项目操作展示：身份选择与患者端

- **Layout**: 左侧一张大截图占位，右侧上下两张小截图占位；底部放四项说明。
- **Title**: 项目操作展示：身份选择与患者端
- **Core message**: 展示多患者入口、患者切换、基础资料和独立历史记录。
- **Content**:
  - 大图：身份选择首页。
  - 小图一：基础资料填写页面。
  - 小图二：侧栏患者切换与历史记录。
  - 说明：三位演示患者、数据隔离、侧栏折叠、未完成问诊恢复。

#### Slide 13 - 项目操作展示：问诊过程

- **Layout**: 三张等宽截图占位，按开放描述、补充追问、诊前档案排列；下方用箭头串联。
- **Title**: 项目操作展示：问诊过程
- **Core message**: 展示患者从自由描述到结构化档案的连续操作过程。
- **Content**:
  - 截图一：开放描述。
  - 截图二：逐项补充追问。
  - 截图三：完成后的诊前档案。
  - 流程说明：自由描述 → 信息抽取 → 单项追问 → 完整度更新 → 生成档案。

#### Slide 14 - 项目操作展示：医生工作台与总结

- **Layout**: 上方大面积医生工作台截图占位；下方三列说明；右下角加入收束句。
- **Title**: 项目操作展示：医生工作台与总结
- **Core message**: 展示医生端如何查看多个患者、问诊详情和决策解释。
- **Content**:
  - 左栏：患者列表与档案数量。
  - 中栏：基础资料、开放描述和问答记录。
  - 右栏：核心字段完成数、关键缺口、下一问来源和停止原因。
  - 收束句：项目通过规则约束Agent，完成安全、可追踪、可解释的诊前信息整理。

## X. Speaker Notes Requirements

- 每页提供中文讲稿，建议总时长12–15分钟。
- 每页讲稿包含：本页目的、关键解释、自然过渡。
- 机制页P08–P10适当展开，操作页P12–P14为截图讲解预留口语提示。
- 不夸大医疗价值，主动说明演示身份、临床验证和权限系统的边界。

## XI. Technical Constraints

- SVG viewBox统一为`0 0 1280 720`。
- 背景使用`<rect>`，换行使用`<tspan>`。
- 禁止`rgba()`、`<style>`、`class`、`foreignObject`、`mask`、`textPath`、脚本和动画。
- 禁止组透明度；透明度写在单个元素上。
- 使用原生Unicode符号；XML保留字符必须转义。
- 每页必须有顶层分组ID，保证PPT可编辑。
- 截图占位框使用原生矩形与文字，不嵌入虚假截图。
