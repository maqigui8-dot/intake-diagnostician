# Completed Record Soft Delete Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 允许患者软删除已完成档案，使其从正常列表隐藏，同时保留整次问诊数据并阻止旧详情访问。

**Architecture:** 在 `intake_reports` 增加 `deleted_at`，Repository 负责患者隔离、幂等删除和查询过滤，FastAPI 映射删除与 `410 Gone` 语义，Vue 侧栏负责确认、请求和界面刷新。未完成问诊的 `archived_at` 逻辑保持独立。

**Tech Stack:** Python 3、FastAPI、SQLAlchemy 2、Alembic、MySQL 8、Vue 3、Vite、Node test runner。

## Global Constraints

- 只软删除已完成档案，不物理删除任何关联数据。
- 第一版不提供已删除列表、恢复、永久删除或批量删除。
- 删除和查询必须限制在当前患者 `demo-zhang`。
- 相同会话再次自动保存不得恢复或复制已删除档案。
- 前端确认文案固定为“该档案将从列表隐藏，已有问诊数据会保留。确定删除吗？”。

---

### Task 1: 档案软删除字段与迁移

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/db.py`
- Create: `backend/migrations/versions/20260917_03_add_report_soft_delete.py`
- Test: `backend/tests/test_db_models.py`

**Interfaces:**
- Produces: `IntakeReport.deleted_at: datetime | None`
- Produces: 数据库版本 `20260917_03`

- [ ] **Step 1: 写失败测试**

在 `test_db_models.py` 断言 `intake_reports.deleted_at` 存在且可空，并将预期 Alembic 版本改为 `20260917_03`。

```python
columns = {item["name"]: item for item in inspect(engine).get_columns("intake_reports")}
self.assertIn("deleted_at", columns)
self.assertTrue(columns["deleted_at"]["nullable"])
```

- [ ] **Step 2: 运行测试并确认因字段和版本缺失而失败**

```powershell
Set-Location backend
python -m unittest tests/test_db_models.py
```

- [ ] **Step 3: 增加模型字段、索引与迁移**

```python
deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

Index(
    "ix_intake_reports_patient_deleted_created",
    IntakeReport.patient_id,
    IntakeReport.deleted_at,
    IntakeReport.created_at,
)
```

迁移 `upgrade()` 增加字段、单列索引和组合索引；`downgrade()` 逆序删除。将 `EXPECTED_DATABASE_REVISION` 更新为 `20260917_03`。

- [ ] **Step 4: 运行模型测试并确认通过**

```powershell
python -m unittest tests/test_db_models.py
```

---

### Task 2: Repository 软删除与查询语义

**Files:**
- Modify: `backend/repository.py`
- Modify: `backend/tests/test_repository.py`

**Interfaces:**
- Produces: `DeletedReport(RuntimeError)`
- Produces: `soft_delete_report(patient_id: str, record_id: str) -> dict[str, str]`
- Changes: `list_patient_reports` 过滤 `deleted_at is null`
- Changes: `get_patient_report` 对已删除档案抛出 `DeletedReport`

- [ ] **Step 1: 写 Repository 失败测试**

覆盖列表过滤、患者隔离、幂等、详情异常、关联数据保留和自动保存不复活：

```python
first = repository.soft_delete_report("patient-a", "record-a")
second = repository.soft_delete_report("patient-a", "record-a")
self.assertEqual(first, second)
self.assertEqual(repository.list_patient_reports("patient-a"), [])
with self.assertRaises(DeletedReport):
    repository.get_patient_report("patient-a", "record-a")
```

再查询 `IntakeSessionModel`、`BaselineMeasurement` 和 `FollowUpAnswer`，断言关联数据仍存在；再次调用 `save_report` 后断言 `deleted_at` 仍不为空且档案总数未增加。

- [ ] **Step 2: 运行测试并确认因接口缺失而失败**

```powershell
python -m unittest tests/test_repository.py
```

- [ ] **Step 3: 实现最小 Repository 行为**

```python
class DeletedReport(RuntimeError):
    pass

def soft_delete_report(self, patient_id: str, record_id: str) -> dict[str, str]:
    with self._session_factory.begin() as database:
        row = database.get(IntakeReport, record_id)
        if row is None or row.patient_id != patient_id:
            raise KeyError("report does not belong to patient")
        if row.deleted_at is None:
            row.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        return {"record_id": row.id, "deleted_at": row.deleted_at.isoformat()}
```

列表查询增加 `IntakeReport.deleted_at.is_(None)`；详情查询先按患者查到行，再对 `deleted_at` 抛出 `DeletedReport`。`save_report` 更新已有行时不得修改 `deleted_at`。

- [ ] **Step 4: 运行 Repository 测试并确认通过**

```powershell
python -m unittest tests/test_repository.py
```

---

### Task 3: FastAPI 删除接口与 410 映射

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/tests/test_database_api.py`

**Interfaces:**
- Consumes: `DeletedReport`、`soft_delete_report`
- Produces: `POST /api/patient/records/{record_id}/delete`
- Produces: 已删除详情的 `410 Gone`

- [ ] **Step 1: 写 API 失败测试**

```python
deleted = await main.delete_patient_record("record-a")
self.assertEqual(deleted["record_id"], "record-a")
response = await main.handle_deleted_report(None, DeletedReport("private"))
self.assertEqual(response.status_code, 410)
self.assertNotIn("private", response.body.decode("utf-8"))
```

覆盖重复删除结果一致、不存在档案返回 `404`、列表不再包含已删除档案。

- [ ] **Step 2: 运行测试并确认因路由与处理器缺失而失败**

```powershell
python -m unittest tests/test_database_api.py
```

- [ ] **Step 3: 实现接口与异常处理**

```python
@app.exception_handler(DeletedReport)
async def handle_deleted_report(_request, _error):
    return JSONResponse(status_code=410, content={"detail": "该档案已删除。"})

@app.post("/api/patient/records/{record_id}/delete")
async def delete_patient_record(record_id: str):
    try:
        return _report_repository.soft_delete_report(DEMO_PATIENT_ID, record_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="记录不存在") from error
```

- [ ] **Step 4: 运行 API 测试并确认通过**

```powershell
python -m unittest tests/test_database_api.py
```

---

### Task 4: 患者侧栏删除交互

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Modify: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Consumes: `POST /api/patient/records/{record_id}/delete`
- Produces: `deleteHistoryRecord(record)` 前端操作
- Produces: `deletingRecordId` 请求状态

- [ ] **Step 1: 写前端失败测试**

```javascript
assert.match(template, /@click\.stop="deleteHistoryRecord\(record\)"/)
assert.match(appSource, /\/api\/patient\/records\/\$\{record\.record_id\}\/delete/)
assert.match(appSource, /该档案将从列表隐藏，已有问诊数据会保留。确定删除吗？/)
assert.match(appSource, /historyDetail\.value\?\.record_id === record\.record_id/)
```

- [ ] **Step 2: 运行测试并确认因删除交互缺失而失败**

```powershell
Set-Location frontend
npm.cmd test
```

- [ ] **Step 3: 实现界面和状态处理**

将单个历史按钮改为包含主按钮与删除按钮的 `article`。实现：

```javascript
async function deleteHistoryRecord(record) {
  if (deletingRecordId.value) return
  if (!window.confirm('该档案将从列表隐藏，已有问诊数据会保留。确定删除吗？')) return
  deletingRecordId.value = record.record_id
  try {
    await request(`/api/patient/records/${record.record_id}/delete`, { method: 'POST' })
    if (historyDetail.value?.record_id === record.record_id) historyDetail.value = null
    await loadHistory()
  } catch (error) {
    formError.value = error.message
  } finally {
    deletingRecordId.value = ''
  }
}
```

样式沿用未完成问诊的两列布局；删除按钮使用低强调度文字，不增加图标。

- [ ] **Step 4: 运行前端测试与构建**

```powershell
npm.cmd test
npm.cmd run build
```

---

### Task 5: 迁移、全量验证与浏览器验收

**Files:**
- Verify: `backend/migrations/versions/20260917_03_add_report_soft_delete.py`
- Verify: all modified backend and frontend files

**Interfaces:**
- Consumes: Tasks 1-4 全部成果
- Produces: 已迁移并通过验收的本地项目

- [ ] **Step 1: 应用 MySQL 迁移**

```powershell
Set-Location backend
python -m alembic upgrade head
```

预期输出包含 `20260916_02 -> 20260917_03`。

- [ ] **Step 2: 运行全量自动化验证**

```powershell
python -m unittest discover -s tests -p "test_*.py"
Set-Location ../frontend
npm.cmd test
npm.cmd run build
```

预期：后端零失败、前端零失败、Vite 构建退出码为 0。

- [ ] **Step 3: 浏览器验收**

打开一条测试档案，点击“删除”，确认二次提示后执行。验证该档案从“已完成档案”列表消失，若详情已打开则自动关闭。

- [ ] **Step 4: 数据库验收**

查询被删除档案的 `deleted_at`，并分别统计其 `intake_sessions`、`baseline_measurements` 和 `follow_up_answers` 关联记录；确认档案已标记删除且关联数据未被物理移除。

