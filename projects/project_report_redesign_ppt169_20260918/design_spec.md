# Design Specification & Content Outline

## I. Project Information
- Project: 中医诊前信息采集与整理系统项目汇报重做版
- Purpose: 组会汇报项目背景、实现方案、核心机制、关键难点与操作效果
- Audience: 课题组老师和组会成员
- Page count: 14
- Core message: 以规则约束 Agent，将患者自由描述整理为可追踪、可解释的诊前资料

## II. Visual Theme
- Academic briefing with Swiss-minimal structure
- Warm cream background, ink green structure, terracotta decision accents
- One visual center per slide; no repetitive card grids
- Cover centered; all other titles top-left

## III. Page Outline
1. 封面：项目名称、汇报人、日期
2. 项目背景与问题：描述零散、重复询问、停止不清、决策难解释
3. 项目目标与定位：结构化、有限追问、停止判断、可追溯；不承担诊断
4. 系统整体架构：Vue 3、FastAPI、Agent+规则、MySQL
5. 系统角色与主要功能：患者端、医生端、patient_id 隔离、只读边界
6. 完整问诊流程：选择患者、基础资料、开放描述、提取、状态、完整度、追问或档案
7. 结构化字段与信息来源：五类字段与问题来源链路
8. 资料完整度如何判断：字段状态、核心缺口、安全缺口、冲突、保护性结束
9. 追问优先级与决策机制：危险信号、核心字段、冲突、高优先普通、可选补充
10. 何时停止追问：继续追问、正常结束、保护性结束
11. 项目实现中的关键难点：轮数、模型不稳定、重复回答、多患者隔离、当前边界
12. 项目操作展示：身份选择与患者端，保留三处截图位
13. 项目操作展示：问诊过程，保留三处截图位
14. 项目操作展示：医生工作台与总结，保留一处大截图位

## IV. Layout Commitments
- P04 vertical four-layer architecture, decision layer emphasized
- P06 bent seven-step path with feedback loop
- P08 central completeness evaluator with inputs and three outcomes
- P09 five-level staircase plus concrete example
- P10 branching decision tree with three outcomes
- P12-P14 solid thin screenshot frames with editorial composition, no dashed placeholders

## V. Speaker Notes
- Chinese notes for every slide
- Mechanism slides receive fuller explanation
- Demo slides include screenshot narration prompts
