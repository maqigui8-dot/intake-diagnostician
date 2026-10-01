# 新版结构化问诊接入中医 Skills 设计

## 目标

保留固定 10 题稳定流程，完成后接入 `tcm-intake` 和 `tcm-zhengxing`，生成信息完整度、红旗风险提示、辨证参考和建议追问。输出只用于诊前整理，不提供处方、剂量、针灸操作或确诊结论。

## 数据流

1. 完成问诊并生成档案。
2. 前端请求 `POST /api/intake/session/{session_id}/analyze`。
3. 后端使用独立会话调用加载了两个 Skill 的 Deep Agent。
4. 前端展示分析；模型不可用时保留基础档案。
5. 保存记录时写入 `skill_analysis`。

## PPT

周报新增第 11 页“中医 Skills 能力接入”，说明接入流程和稳定性设计。
