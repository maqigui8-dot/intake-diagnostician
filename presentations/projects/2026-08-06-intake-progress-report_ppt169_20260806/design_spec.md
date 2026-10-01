# 中医诊前问诊系统进展汇报 Design Spec

## I. Project Context

- Purpose: 汇报本轮围绕诊前信息完整度、动态补问、检查建议和工程稳定性的改造进展。
- Audience: 课题组与项目组成员。
- Scenario: 组会现场，8-10 分钟中文汇报。
- Canvas: PPT 16:9，1280x720。
- Page count: 8。

## II. Narrative Mode

- Mode: briefing。
- Titles use neutral topic labels and expose the complete set of changes for quick scanning。
- Structure: 反馈目标 -> 新流程 -> Skill 分工 -> 动态补问 -> 分析收敛 -> 工程验证 -> 下一步。

## III. Visual Direction

- Style: soft-rounded，成熟医疗产品内部汇报感。
- Shape language: 12-16px 圆角、扁平卡片、轻量边框、稳定栅格。
- Rhythm: 信息页紧凑，流程页留白，封面与结尾形成前后呼应。
- Avoid: 营销式大字堆叠、泛化医疗照片、过多装饰、单一绿色铺满。

## IV. Font Plan

- Default stack: "Microsoft YaHei", Arial, sans-serif。
- Code stack: Consolas, "Courier New", monospace。
- Cover 52px; page title 34px; subtitle 24px; body 20px; annotation 14px。
- Chinese text keeps zero letter spacing and uses manual line breaks。

## V. Color Plan

- Background #F7F9F5; secondary background #EAF2E8; surface #FFFFFF。
- Primary #2F6B4F; secondary accent #4C8C7A; progress accent #D6A84B。
- Main text #1F2A24; secondary text #657269; border #DCE5DC。
- Accent is limited to status, key numbers, and process checkpoints。

## VI. Page Roster

- P01 cover, anchor, native SVG with product screenshot accent。
- P02 feedback and target adjustment, dense, four requirement cards。
- P03 new pre-consultation workflow, breathing, horizontal process flow。
- P04 two Skill responsibilities, dense, balanced two-column comparison。
- P05 adaptive follow-up loop, breathing, circular loop plus rule callouts。
- P06 analysis output scope, dense, included/excluded comparison and exam reference image。
- P07 engineering and validation, dense, implementation chain plus evidence metrics。
- P08 current conclusion and next steps, anchor, completed/next two-column close。

## VII. Visualization Reference List

- P03: custom process flow, no-template-match。
- P05: custom closed-loop diagram, no-template-match。
- P07: custom architecture strip and KPI cards, no-template-match。
- No catalog chart template is required because the deck reports workflow and implementation rather than a numerical time series。

## VIII. Image Resource Inventory

| Filename | Size | Ratio | Intent | Usage | Type | Status |
|---|---:|---:|---|---|---|---|
| project-home.png | 1440x1000 | 1.44 | accent | P01 product interface proof | screenshot | existing |
| exam-reference.jpg | 1279x1706 | 0.75 | side-by-side | P06 source context for recommended exams | photo/document | existing |

## IX. Content Outline

- P01 中医诊前问诊系统进展汇报。Core message: 本轮迭代覆盖完整度判断、动态补问与检查建议。
- P02 组会反馈与目标调整。Core message: 完整度标准和分析边界已经重新定义。
- P03 新的诊前问诊流程。Core message: 从固定问卷升级为可迭代的诊前信息闭环。
- P04 两个 Skill 如何分工。Core message: 一项决定问什么，一项决定怎么问。
- P05 动态补问闭环。Core message: 每轮只补一个关键缺口，并在回答后重新评估。
- P06 智能分析内容收敛。Core message: 仅保留信息完整度与推荐检查项目，明确安全边界。
- P07 工程实现与稳定性。Core message: 单次模型调用、后台执行、超时重试和结构化保存已经落地并通过验证。
- P08 当前结论与下一步。Core message: 核心改造已完成，下一阶段进入规则细化和真实场景验证。

## X. Speaker Notes Plan

- Notes use concise spoken Chinese, 45-70 seconds per page。
- Explain reason, implementation and evidence; avoid reading every bullet verbatim。
- No diagnosis, prescription or medical efficacy claims。

## XI. Quality and Compliance

- Every SVG root must contain width="1280", height="720", and viewBox="0 0 1280 720"。
- All direct SVG children are semantic groups with ids。
- All visible content and notes avoid personal titles and hierarchy wording。
- Use only locked colors, fonts, icons and image files。
- Run SVG quality check, finalize, export, render all slides and run slides_test.py before delivery。
