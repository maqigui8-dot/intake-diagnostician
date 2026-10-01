# Learning and Project Report - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | 前期学习与成人肥胖诊前问诊系统汇报 |
| Canvas | PPT 16:9, 1280 x 720 |
| Page Count | 32 |
| Audience | 课题组汇报 |
| Narrative | 学习积累 → 能力迁移 → 当前项目实践 |

## II. Content Strategy

- 前 20 页只呈现已学习和已完成的内容，不把基本要求包装成已完成成果。
- 将前期“辨证与开方”的原型作为技术学习案例，明确当前项目已将产品目标收敛为诊前信息采集、风险提示与医生核对。
- 后 11 页延续现有项目汇报，展示成人肥胖诊前问诊系统的当前实现。

## III. Visual Direction

- Mode: briefing
- Visual style: editorial
- Background: #F7F9F6
- Primary: #155E47
- Accent: #E07A5F
- Font: Microsoft YaHei, Arial, sans-serif
- Use flat editorial composition with one main idea per page. No decorative imagery.

## IV. Page Roster

| Page | Title | Core message |
| --- | --- | --- |
| P01 | 前期学习与能力准备 | 学习阶段为当前医疗 AI 项目建立技术底座。 |
| P02 | 学习任务与路线 | 前后端、AI 接口和 Agent 三条线并行推进。 |
| P03 | 已完成学习成果总览 | 从页面交互、服务接口到智能体均有可运行练习。 |
| P04 | 能力迁移路径 | 技术学习逐步指向医疗场景中的可靠采集。 |
| P05 | 前端学习 | 掌握 HTML、CSS、JavaScript 与 Vue 基础。 |
| P06 | Todo List 练习 | 用完整交互练习 Vue 响应式开发。 |
| P07 | 前端能力沉淀 | 状态、事件、渲染与持久化可迁移到业务页面。 |
| P08 | 后端学习 | 用 FastAPI 建立接口、规则和数据交互基础。 |
| P09 | BMI 计算器 | 完成前端输入、后端计算和 JSON 返回的闭环。 |
| P10 | 规则计算的启发 | 关键数值应由确定性规则计算，而非由模型猜测。 |
| P11 | 大模型 API 原型 | 完成症状与舌象输入到结构化结果的接口探索。 |
| P12 | 结构化输出与可靠性 | 环境变量、模型调用、JSON 解析和参数校验形成服务边界。 |
| P13 | Agent 平台级入门 | 使用 Dify、Ollama 和模型调用完成平台级实践。 |
| P14 | RAG 知识库流程 | 跑通资料上传、检索、拼接提示词和回答引用。 |
| P15 | 克隆老中医原型 | 用多轮追问和结构化总结练习对话流程。 |
| P16 | Function Calling 与 MCP | 让 Agent 在需要时调用外部工具。 |
| P17 | LangChain RAG | 脱离平台理解 RAG 全链路模块。 |
| P18 | LangGraph 持久记忆 | 用状态图和数据库支持复诊信息延续。 |
| P19 | DeepAgents 实践 | 组合工具、记忆和流程编排形成智能体原型。 |
| P20 | 从能力探索到安全收敛 | 将学习原型转化为面向医生的诊前采集系统。 |
| P21-P32 | 当前项目实践 | 延续已完成的成人肥胖诊前问诊系统汇报。 |

## V. Image Resources

| Filename | Purpose | Pages |
| --- | --- | --- |
| shot-baseline.png | 基础资料页面 | P26 |
| shot-followup.png | 对话式追问页面 | P30 |
| shot-result.png | 患者端结果 | P31 |
| shot-doctor.png | 医生端结果 | P31 |

## VI. Technical Constraints

- Every SVG root includes width="1280", height="720", and viewBox="0 0 1280 720".
- Only use the colors, font and images locked in spec_lock.md.
- Do not use rgba(), style tags, foreignObject, script, symbol plus use, or g opacity.
- Screenshots use preserveAspectRatio="xMidYMid meet".
