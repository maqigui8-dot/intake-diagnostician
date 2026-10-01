# 成人肥胖诊前问诊系统 - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 成人肥胖诊前问诊系统项目进展汇报 |
| **Canvas Format** | PPT 16:9 (1280 × 720) |
| **Page Count** | 10 |
| **Design Style** | briefing + editorial，轻量医疗研究简报 |
| **Target Audience** | 组会中的导师、学长和同组同学 |
| **Use Case** | 展示本周项目改造、当前完整流程与下一步重点 |
| **Content Strategy** | balanced default：围绕已实现的结构化问诊能力重组表达，不引入外部事实。 |
| **Created Date** | 2026-08-20 |

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280 × 720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 64px，上下 52px |
| **Content Area** | 1152 × 616px |

## III. Visual Theme

### Theme Style

- **Mode**: briefing。以“问题、改造、流程、成果、下一步”为顺序，适合组会的完整项目进展说明。
- **Visual style**: editorial。标题层级清晰，使用细分隔线、克制留白和少量信息模块。
- **Theme**: Light theme。
- **Tone**: 专业、克制、可验证；医疗感来自配色和真实产品截图，而非装饰性元素。

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F7F9F6` | 页面背景 |
| **Secondary bg** | `#EAF2EB` | 截图框与信息区底色 |
| **Primary** | `#155E47` | 标题、主路径、图标 |
| **Accent** | `#E07A5F` | 风险、问题、关键变化 |
| **Secondary accent** | `#4C8C7B` | 次级节点、分层提示 |
| **Body text** | `#15221C` | 正文 |
| **Secondary text** | `#5E6D65` | 注释与说明 |
| **Border/divider** | `#C9D7CE` | 分隔线 |
| **Success** | `#2E8B57` | 已完成和验证通过 |
| **Warning** | `#C94A3D` | 问题与风险标记 |

## IV. Typography System

**Typography direction**: 中文优先的清晰汇报体，投影环境下保持稳定可读。

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | Microsoft YaHei | Arial | sans-serif |
| **Body** | Microsoft YaHei | Arial | sans-serif |
| **Emphasis** | Microsoft YaHei | Arial | sans-serif |
| **Code** | — | Consolas | monospace |

**Per-role font stacks**:

- Title: `"Microsoft YaHei", Arial, sans-serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: `"Microsoft YaHei", Arial, sans-serif`
- Code: `Consolas, "Courier New", monospace`

**Baseline**: Body font size = 20px. Cover title 68px，page title 38px，subtitle 25px，annotation 14px。

## V. Layout Principles

- Header: 90px，高对比页面标题与细线定位。
- Content: 540px，以单一主视觉或明确的左右结构呈现。
- Footer: 36px，页码与“成人肥胖诊前问诊系统”标记。
- 多信息页面使用 2–4 个扁平信息块；概念页使用裸文本、分隔线和留白，避免每页均为卡片墙。
- 产品截图保持完整可读，使用浅绿色边框和图注，不裁切界面关键区域。

## VI. Icon Usage Specification

- **Built-in icon library**: `tabler-outline`，stroke width 2。
- **Approved inventory**: `stethoscope`, `clipboard-list`, `message-circle`, `shield-check`, `route`, `chart-bar`, `file-text`, `checks`, `brain`, `alert-circle`, `arrow-right`, `user`。

## VII. Visualization Reference List

本汇报不使用数据型图表模板。所有流程和分层关系均使用原生 SVG 的简洁路径、节点和文字表达，避免无来源数据可视化。

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| shot-baseline.png | 2736 × 1200 | 2.28:1 | 展示基础资料采集页面 | Product screenshot | full-width framed screenshot | user | Existing | 项目当前患者端截图 | none | P06 |
| shot-followup.png | 2736 × 1200 | 2.28:1 | 展示对话式追问页面 | Product screenshot | full-width framed screenshot | user | Existing | 项目当前患者端截图 | none | P08 |
| shot-result.png | 2736 × 1200 | 2.28:1 | 展示患者端结果与档案 | Product screenshot | framed screenshot | user | Existing | 项目当前患者端截图 | none | P09 |
| shot-doctor.png | 2736 × 1200 | 2.28:1 | 展示医生端分层摘要 | Product screenshot | framed screenshot | user | Existing | 项目当前医生端截图 | none | P09 |

## IX. Content Outline

### P01 封面：成人肥胖诊前问诊系统
- **Core message**: 从普通聊天问诊升级为可追溯的规则驱动诊前采集。
- **Layout**: breathing，左侧大标题，右侧以四层路径为主视觉。

### P02 项目目标：为诊中服务，而不是在线确诊
- **Core message**: 系统整理诊前资料，为医生诊中判断、禁忌核查与检查准备提供输入。
- **Layout**: breathing，三段式“患者输入—系统整理—医生确认”。

### P03 改造前的核心问题
- **Core message**: 固定式问答、状态刷新依赖、完整度不可靠，难以形成可用档案。
- **Layout**: dense，三个问题区域加一条结论线。

### P04 改造原则：规则负责判断，AI负责理解
- **Core message**: LLM 不直接计算执行度或结束问诊；确定性规则掌握完成门槛。
- **Layout**: breathing，对照式角色分工。

### P05 当前完整流程
- **Core message**: 基础资料 → 开放描述 → 分层追问 → 诊前档案与检查候选。
- **Layout**: dense，五步横向流程。

### P06 第一步：基础资料与成人 BMI 规则
- **Core message**: 年龄、性别、身高、体重是硬性前置；BMI 和腰围提示由后端确定性计算。
- **Layout**: breathing，真实基础资料页面截图 + 三条规则说明。

### P07 完整度模型：四层门槛共同决定何时问够
- **Core message**: 基础资料必须就绪，病因风险 ≥80%，中医资料 ≥70%，安全资料 100%。
- **Layout**: dense，四层阶梯与停止条件。

### P08 对话式追问：自然、可解释、可继续
- **Core message**: 澄清不算医学证据；不按固定轮数结束；AI 不可用时仍可用固定问题继续采集。
- **Layout**: breathing，真实对话追问截图 + 三条行为约束。

### P09 双端结果：患者安全展示，医生掌握执行依据
- **Core message**: 患者只见安全结果，医生可见分层执行度、证据、矛盾与检查候选。
- **Layout**: dense，患者端与医生端真实截图并列。

### P10 当前成果与下一步
- **Core message**: 已完成关键流程和测试验证，下一阶段转向隐私权限、真实浏览器流程和文档收口。
- **Layout**: anchor，两个验证数字 + 三项下一步。

## X. Speaker Notes

每页备注包含一句口播重点。内部事实来源为当前项目的 `Task 4–8 Report`、后端与前端测试结果、以及成人肥胖诊前问诊实施计划；不加入外部未核实数据。

## XI. Tech Constraints

## XII. Approved Amendment — Stop Condition Page

- Insert a new page after P07: **P08 什么时候问够了：追问结束条件**.
- Core message: the system does not stop after a fixed number of turns. It ends only when hard prerequisites are met, the current clinical branch meets its completeness requirement, no key risk or contradiction remains unresolved, and an unknown or refusal has been clarified once and recorded.
- Decision rule: all conditions met → generate the pre-visit profile; otherwise → continue with the highest-priority missing field.
- Existing pages are renumbered: P08 → P09, P09 → P10, P10 → P11.

- 每页 SVG 根元素必须包含 `width="1280"`、`height="720"` 与 `viewBox="0 0 1280 720"`。
- 仅使用 spec_lock.md 中锁定的颜色、字体、图标和截图。
- 禁止 `rgba()`、`<style>`、`<foreignObject>`、`<script>`、`<g opacity>` 和未转义 XML 文本。
- 所有截图保持 `preserveAspectRatio="xMidYMid meet"`，不得裁去 UI 关键信息。
