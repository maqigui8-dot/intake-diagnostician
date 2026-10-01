# 未完成问诊续接与软归档实施计划

> 设计依据：`docs/superpowers/specs/2026-09-16-unfinished-intake-resume-design.md`

## 目标

在现有 MySQL 完整持久化基础上，增加未完成问诊列表、跨页面恢复和软归档功能，并确保归档数据仍可审计、旧链接不能继续修改。

## 实现原则

- 以 `intake_sessions` 为未完成问诊唯一事实来源。
- 先写失败测试，再写最小实现。
- Repository 负责持久化与患者隔离，FastAPI 路由负责 HTTP 语义，Vue 负责交互状态。
- 不物理删除会话或关联数据。

## 任务 1：增加归档字段和数据库迁移

文件：

- 修改 `backend/models.py`
- 新增 `backend/migrations/versions/20260916_02_add_session_archiving.py`
- 修改 `backend/tests/test_db_models.py`

步骤：

1. 在模型测试中断言 `IntakeSessionModel` 存在可空的 `archived_at` 字段。
2. 运行模型测试，确认失败。
3. 在 SQLAlchemy 模型中增加 `archived_at`。
4. 新增 Alembic 迁移：添加字段及 `(patient_id, archived_at, updated_at)` 索引。
5. 再次运行模型测试。

验证命令：

```powershell
python -m unittest backend/tests/test_db_models.py
```

## 任务 2：实现 Repository 查询、归档和归档保护

文件：

- 修改 `backend/repository.py`
- 修改 `backend/tests/test_repository.py`

步骤：

1. 增加失败测试，覆盖：
   - 只列出有实际填写行为的未完成会话。
   - 排除已结束、已有报告和已归档会话。
   - 按 `updated_at` 倒序。
   - 患者隔离。
   - 归档幂等且只增加一次审计事件。
   - 归档后关联问答仍存在。
   - 读取归档会话时抛出明确异常。
2. 运行测试确认失败。
3. 增加 `ArchivedSession` 异常。
4. 实现 `list_unfinished_sessions(patient_id)`，返回精简 DTO。
5. 实现 `archive_session(patient_id, session_id)`，事务内设置 `archived_at`、更新快照、追加审计并递增版本。
6. 在 `get_or_create_session` 和 `save_session_state` 中拒绝已归档会话。
7. 运行 Repository 测试确认通过。

验证命令：

```powershell
python -m unittest backend/tests/test_repository.py
```

## 任务 3：暴露患者接口并映射 HTTP 错误

文件：

- 修改 `backend/main.py`
- 修改 `backend/tests/test_database_api.py`

步骤：

1. 增加失败测试，覆盖未完成列表接口、归档接口、归档幂等和 `410 Gone`。
2. 运行 API 测试确认失败。
3. 增加：
   - `GET /api/patient/sessions/unfinished`
   - `POST /api/intake/session/{session_id}/archive`
4. 将 `ArchivedSession` 映射为不泄露内部信息的 `410` 响应。
5. 对归档入口做当前演示患者的归属校验。
6. 运行 API 测试确认通过。

验证命令：

```powershell
python -m unittest backend/tests/test_database_api.py
```

## 任务 4：提取前端未完成会话状态逻辑

文件：

- 新增 `frontend/src/unfinished-sessions.js`
- 新增 `frontend/tests/unfinished-sessions.test.mjs`

步骤：

1. 编写失败测试，覆盖：
   - 当前会话从侧栏列表中过滤。
   - 切换会话时生成正确 URL。
   - 阶段标签及时间展示所需的纯函数行为。
2. 运行前端测试确认失败。
3. 实现最小纯函数模块，避免将关键规则埋在 Vue 组件中。
4. 再次运行测试确认通过。

验证命令：

```powershell
Set-Location frontend
npm test
```

## 任务 5：实现侧栏“继续问诊”与软归档交互

文件：

- 修改 `frontend/src/App.vue`
- 修改 `frontend/src/style.css`
- 修改 `frontend/tests/patient-visibility.test.mjs`

步骤：

1. 在静态前端测试中增加失败断言，覆盖两个分区、恢复方法、归档方法、确认文案和新接口地址。
2. 运行测试确认失败。
3. 在 `App.vue` 增加未完成会话状态、加载函数和派生列表。
4. 页面初始化时加载未完成会话。
5. 基础资料、开放描述、补充回答和正式档案保存成功后刷新列表。
6. 实现点击恢复：切换 `sessionId`、更新 URL、清理临时状态并加载会话。
7. 实现归档确认与请求；归档当前会话后调用现有新建流程。
8. 处理 `410`：提示已归档并进入新问诊。
9. 调整侧栏样式，保持当前简洁中医工作台风格，不增加多余图标。
10. 运行前端测试和构建。

验证命令：

```powershell
Set-Location frontend
npm test
npm run build
```

## 任务 6：应用迁移并执行全量自动化验证

文件：

- 不新增业务文件；验证已有迁移与测试。

步骤：

1. 对本地 MySQL 执行 `alembic upgrade head`。
2. 检查 `intake_sessions.archived_at` 和新索引存在。
3. 运行全部后端测试。
4. 运行全部前端测试和生产构建。
5. 若有回归，先补充能够重现问题的测试再修复。

验证命令：

```powershell
Set-Location backend
python -m alembic upgrade head
python -m unittest discover -s tests -p "test_*.py"
Set-Location ../frontend
npm test
npm run build
```

## 任务 7：浏览器和数据库联合验收

步骤：

1. 打开患者端，新建并填写一条未完成问诊。
2. 新建第二条问诊，确认第一条出现在“继续问诊”。
3. 点击第一条，确认恢复正确阶段和内容。
4. 刷新浏览器并重启后端，确认仍可恢复。
5. 放弃当前会话，确认二次提示和自动新建行为。
6. 访问旧链接，确认提示已归档且无法继续填写。
7. 查询 MySQL，确认 `archived_at`、审计事件和关联问答均保留。
8. 记录最终自动化测试数量与浏览器验收结果。

