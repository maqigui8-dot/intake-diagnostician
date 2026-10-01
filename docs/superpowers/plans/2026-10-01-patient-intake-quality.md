# Patient Intake Quality Implementation Plan

> **For agentic workers:** 本任务由当前对话直接执行；使用 test-driven-development 逐项验证，不派生子任务。当前目录不是 Git 仓库，因此不执行提交步骤。

**Goal:** 建立可重复评测，增加患者确认纠错，收敛旧接口与结果展示。

**Architecture:** 评测集在 `backend/evaluation` 中只读运行现有规则。纠错通过患者作用域 API 写入原会话并保留审计，前端在自动保存前加入确认阶段。旧接口清理以真实调用关系和回归测试为准。

**Tech Stack:** Python/FastAPI/unittest、Vue 3/Node test、MySQL/SQLAlchemy。

## Global Constraints

- 只使用虚构评测病例，不删除现有患者资料。
- 不输出自动诊断、处方或治疗建议。
- 演示患者选择不是鉴权，真实数据上线不在本计划范围内。
- 每项先观察测试失败，再实现并验证。

---

### Task 1: 固定离线评测集

**Files:** `backend/evaluation/cases.json`, `backend/evaluation/runner.py`, `backend/tests/test_evaluation.py`, `README.md`

**Interfaces:** `load_cases() -> list[dict]`；`evaluate_cases(cases) -> dict`；命令 `python -m evaluation.runner` 输出 JSON 摘要与失败 ID。

- [x] 写测试：病例数量至少 30，ID 唯一，合成数据标记；正负例有明确期望。
- [x] 运行 `python -m unittest tests.test_evaluation -q`，确认因新接口缺失而失败。
- [x] 实现 40 个单轮/停止病例与 30 组离线多轮会话，调用实际本地规则。
- [x] 再运行测试和评测命令，记录真实通过率及适用范围。

### Task 2: 服务端确认与纠错

**Files:** `backend/intake_flow.py`, `backend/intake_views.py`, `backend/main.py`, `backend/tests/test_intake_flow.py`, `backend/tests/test_database_api.py`

**Interfaces:** 患者作用域字段纠错接口；患者状态返回可确认的字段标签、值和状态；现有保存接口由服务端再次校验。

- [x] 写测试：纠错保留原问答和审计、重建报告、重新判定完整度、危险信号不可抹除、他人会话不可修改。
- [x] 运行目标测试并确认失败原因正确。
- [x] 实现最小服务端功能并运行目标测试。

### Task 3: 前端确认页

**Files:** `frontend/src/App.vue`, `frontend/src/follow-up-stage.js`, `frontend/src/style.css`, `frontend/tests/follow-up-stage.test.mjs`, `frontend/tests/patient-visibility.test.mjs`

**Interfaces:** 完成问诊显示确认页；患者修改上述五类关键字段；点击确认后调用保存接口；错误保留在原页。

- [x] 写测试：完成后不自动保存、确认区展示字段与纠错入口、未确认不可保存。
- [x] 运行目标测试确认失败。
- [x] 实现 UI 和请求，运行目标测试与构建。

### Task 4: 收敛旧接口与结果页

**Files:** `backend/main.py`, `backend/tests/test_multi_patient_api.py`, `frontend/src/App.vue`, `frontend/tests/patient-visibility.test.mjs`, `README.md`

**Interfaces:** 仅保留当前患者端必需的公开路径；结果显示已确认/待确认/无法确认的说明。

- [x] 先列出前端实际调用路径与旧接口测试，写路由边界失败测试。
- [x] 运行目标测试确认失败。
- [x] 移除无调用的匿名旧路由注册，保留内部函数与历史数据；更新文档。
- [x] 全量运行后端测试、前端测试、前端构建与两套评测命令。
