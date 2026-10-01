# Design Specification & Content Outline

## I. Project Information

- Project: 成人肥胖中医诊前智能问诊系统组会汇报
- Purpose: 在10—12分钟内说明项目背景、问题来源、结构化字段模型、完整度判断、停止追问机制、关键技术实现与操作流程。
- Audience: 课题组教师、临床与技术方向组会成员。
- Language: 简体中文。
- Page count: 14页。
- Content strategy: 严格保留用户确认的14页顺序与标题，平衡压缩内容，不引入项目之外的新事实。
- Core message: 项目通过“大模型理解自然语言、确定性规则控制流程”，把患者零散表达整理为有证据、有完整度判断和停止条件的诊前档案。

## II. Canvas Specification

- Format: PPT 16:9。
- ViewBox: 1280 × 720。
- Safe area: 左右各64px，上下各46px。
- Default title zone: y=48—112。
- Default content zone: y=132—654。
- Footer: 页码位于右下，必要时配短页签，不使用重复项目全称。

## III. Visual Theme

- Mode: briefing。用户已提供权威页序，页面使用中性、完整、可扫描的组会简报语气。
- Visual style: editorial。采用清晰的标题层级、细分隔线、窄色条、留白和少量强调色，不使用大面积卡片阵列。
- Background: 暖米白 `#F7F5EF`，主要内容面使用白色或浅绿灰。
- Primary: 临床墨绿 `#174C43`，用于标题、流程主线与核心判断。
- Accent: 暖棕 `#C76B3C`，仅用于问题、风险和停止条件提示。
- Secondary accent: `#6E9184`，用于辅助层级和已确认状态。
- Texture: 纯色平面，无投影；以细线和版心组织信息。

## IV. Typography Plan

- Cover title: `"Microsoft YaHei", Arial, sans-serif`, 54px, bold。
- Slide title: `"Microsoft YaHei", Arial, sans-serif`, 36px, bold。
- Subtitle: `"Microsoft YaHei", Arial, sans-serif`, 26px。
- Body: `"Microsoft YaHei", Arial, sans-serif`, 20px，行距1.45。
- Annotation: `"Microsoft YaHei", Arial, sans-serif`, 14px。
- Emphasis: 使用粗体与强调色，不使用斜体。
- Code/logic expression: `Consolas, "Courier New", monospace`。
- Formula policy: text-only；本汇报不包含需要LaTeX渲染的公式。

## V. Layout System

- 页面以单一主构图为主，避免仪表盘式小卡片堆叠。
- 信息页优先使用两栏、三栏、表格、横向流程和上下分区。
- 每页标题下设置细墨绿规则线，页码统一放右下角。
- 核心判断使用大号公式式文字或中央结构，不使用复杂图表。
- 第12—14页保留70%以上面积作为截图占位区；占位框使用浅底、虚线边框和明确图片说明。
- 相邻页面轮廓需变化：两栏、流程、分层表、状态更新、停止条件、实现表、截图页交替。

## VI. Icon Plan

- Library: tabler-outline，统一2px线宽。
- Approved inventory: clipboard-list, message-chatbot, shield-check, file-description, database, search, alert-triangle, circle-check, stethoscope, history, user, list-details, route, arrows-split, brain, forms。
- Icons只用于标记信息类型和步骤，尺寸24—42px，不承担主要叙事。
- 不混用其他图标库，不使用Emoji。

## VII. Visualization Reference List

- 本汇报不使用数据统计图。
- P04使用自绘横向业务流程。
- P05使用三源汇流结构。
- P07使用四层完整度结构。
- P09使用“原话—字段—状态—判断”流程。
- P10使用“继续追问/正常停止/保护性停止”三分逻辑结构。
- P11使用三列表格。

## VIII. Image Resource List

| Page | Type | Acquire Via | Status | Placement |
|---|---|---|---|---|
| P12 | 基础资料页面截图 | placeholder | Placeholder | 单张大图，占页面主体 |
| P13 | 自由描述与动态追问截图 | placeholder | Placeholder | 两张并列 |
| P14 | 患者端结果与医生端档案截图 | placeholder | Placeholder | 两张并列 |

- 其他页面不使用外部图片，不需要来源标注。
- 截图占位框必须保留清晰边界与替换提示，方便用户在PowerPoint中覆盖。

## IX. Content Outline

### P01 成人肥胖中医诊前智能问诊系统
- Core message: 基于核心信息完整度的动态追问与诊前档案生成。
- Content: 主标题、副标题、汇报人/课题组/日期占位。
- Layout: 左侧标题，右侧以抽象问诊路径线条和三个关键词“理解 / 判断 / 整理”构成视觉锚点。

### P02 成人肥胖诊前问诊面临的信息采集问题
- Core message: 自然表达、固定问卷和医生时间之间存在结构性矛盾。
- Content: 患者表达零散；固定问卷不能动态调整；过少遗漏、过多增加负担；核心研究问题。
- Layout: 左侧问题链，右侧放大核心研究问题。

### P03 项目定位：诊前信息整理，而非自动诊断
- Core message: 系统整理信息并提示风险，不替代医生诊断、辨证和治疗。
- Content: 系统负责与系统不负责的边界。
- Layout: 中央边界线，两侧对照，底部一句定位语。

### P04 从患者填写到医生查看的完整流程
- Core message: 每轮回答后重新提取信息、更新状态并判断是否继续。
- Content: 八步主流程与患者端、决策引擎、医生端三个阶段。
- Layout: 横向流程，阶段以细色带分组。

### P05 问诊问题从哪里来？
- Core message: 问题由成人肥胖评估、中医问诊框架和医疗安全要求共同构建。
- Content: 三类来源及代表字段；强调大模型不自由决定医疗采集范围。
- Layout: 三列来源汇入底部统一字段体系。

### P06 如何把问诊内容转化为可计算的信息字段
- Core message: 每个临床问题被转为带状态、优先级、证据和冲突记录的字段。
- Content: 字段属性列表、六种状态、五行示例表。
- Layout: 左侧字段解剖，右侧状态图例与示例。

### P07 信息完整度如何判断？
- Core message: 完整度是四层核心信息的可用性判断，而不是简单总分。
- Content: 基础资料、病程风险、核心中医症状、安全信息；四项额外阻塞条件。
- Layout: 四层垂直结构，右侧阻塞检查清单。

### P08 为什么不要求患者回答所有问题？
- Core message: 区分患者完成线与医生完善线，避免可选细节无限延长问诊。
- Content: 两条完成线及设计原则。
- Layout: 左右两条轨道，中间用分界箭头标示“在线完成”与“诊中补充”。

### P09 一次患者回答如何影响完整度？
- Core message: 一句患者原话可以同时更新多个字段，完整度随有效证据变化。
- Content: 示例原话、三个字段状态变化、七步系统处理。
- Layout: 顶部原话引文，下方三字段更新，底部重新判断流程。

### P10 系统何时继续追问，何时停止？
- Core message: 系统同时支持继续追问、正常停止和保护性停止三种结果。
- Content: 各自触发条件；正常停止逻辑表达；保护性输出。
- Layout: 三栏逻辑分区，中栏正常停止更突出。

### P11 关键技术问题与当前实现
- Core message: 五类关键问题均有工程处理机制，但真实准确性仍需标准病例和临床评价。
- Content: 难点、处理方式、当前状态三列表格。
- Layout: 全宽表格，底部临床验证边界提示。

### P12 项目操作展示（一）：建立患者基础资料
- Core message: 基础资料确认后完成BMI评估并进入问诊。
- Content: 一句说明、单张大截图占位、四步底部流程。
- Layout: 75%大图占位。

### P13 项目操作展示（二）：根据核心信息缺口动态追问
- Core message: 系统从自由描述提取已有信息，并针对核心缺口继续追问。
- Content: 两张并列截图占位及短说明。
- Layout: 左右截图各约45%。

### P14 项目操作展示（三）：生成并保存诊前档案
- Core message: 核心信息达到可用状态后，生成患者端与医生端两种视图。
- Content: 两张并列截图占位、双端说明、收束语。
- Layout: 左右截图各约45%，底部收束。

## X. Speaker Notes Plan

- 每页2—4句自然口语，避免照读页面文字。
- P02明确研究问题；P05说明问题来源；P07—P10为汇报核心，适当延长讲解。
- P11主动区分“工程实现”与“临床验证”。
- P12—P14使用操作动作描述，便于用户插入截图后同步讲解。
- 总时长控制在10—12分钟。

## XI. Technical Constraints

- 所有SVG必须使用`viewBox="0 0 1280 720"`。
- 只使用spec_lock中声明的颜色、字体和图标。
- 禁止`rgba()`、CSS class、foreignObject、textPath和脚本。
- XML保留字符必须正确转义。
- 正文字号原则上不低于18px，截图说明不低于16px。
- 所有文本必须位于安全区内，不得出现裁切或重叠。
- 第12—14页截图占位使用虚线边框，不嵌入任何实际截图。
