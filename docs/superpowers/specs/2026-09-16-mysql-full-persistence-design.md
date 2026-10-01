# MySQL 完整持久化设计

## 目标

将当前内存会话和本地 JSON 档案升级为 MySQL 持久化，使问诊会话在服务重启后仍可恢复，并为多患者隔离、纵向历史、医生审核和效果评估提供结构化数据基础。

## 范围

本次改造覆盖患者、问诊会话、基础测量、字段状态、追问回答、推荐检查、最终报告和审计事件。保留现有问诊规则、完整度计算、动态选题和停止策略的业务语义。

本次不实现登录认证、医生工作台编辑功能和正式生产部署；数据库结构为这些功能预留扩展位置。

## 技术方案

- ORM：SQLAlchemy 2.0
- 迁移工具：Alembic
- MySQL 驱动：PyMySQL
- 配置：通过 `DATABASE_URL` 环境变量注入
- 默认连接格式：`mysql+pymysql://user:password@127.0.0.1:3306/intake_diagnostician?charset=utf8mb4`
- 测试：Repository 单元测试使用 SQLite 临时数据库；MySQL 集成测试由独立标记控制

## 架构边界

```text
FastAPI 路由
    ↓
问诊应用服务
    ↓
Repository 仓储接口
    ↓
SQLAlchemy Session
    ↓
MySQL
```

问诊规则保持在 `intake_execution.py`、`intake_question_policy.py`、`skill_analysis.py` 等领域模块中。Repository 仅负责读取和保存，不负责计算完整度、选择问题或决定停止。

## 数据模型

### patients

- `id`：字符串主键
- `display_name`：患者显示名，可空
- `created_at`、`updated_at`

初始版本继续使用 `demo-zhang` 作为默认患者，但所有查询必须显式携带 `patient_id`，不允许跨患者读取。

### intake_sessions

- `id`：会话 ID
- `patient_id`：外键
- `phase`：当前阶段
- `turn`：当前轮次
- `open_answer`、`latest_answer`
- `current_question`、`current_field_key`、`attempt_number`
- `stop_reason`
- `rule_version`
- `context_json`
- `blocking_keys_json`
- `conflicts_json`
- `safety_alerts_json`
- `version`：乐观锁版本
- `created_at`、`updated_at`

`patient_id + id` 建立唯一约束。每次状态更新递增 `version`，防止重复提交覆盖新状态。

### baseline_measurements

- `session_id`：唯一外键
- 年龄、性别、身高、体重、腰围、臀围、测量时间
- BMI、BMI 分级、中心性肥胖判断、患者安全文案
- `created_at`、`updated_at`

### intake_field_states

- `session_id`、`field_key`：联合唯一键
- `status`
- `attempts`
- `evidence_json`
- `conflicts_json`
- `first_confirmed_turn`、`last_updated_turn`
- `created_at`、`updated_at`

字段定义、权重和优先级继续来自代码中的规则注册表，不复制到每条会话记录。

### follow_up_answers

- 自增主键
- `session_id`
- `sequence_no`
- `question_key`、`question_kind`
- `question`、`answer`
- `attempt_number`、`answer_quality`
- `created_at`

`session_id + sequence_no` 建立唯一约束，保持问答顺序稳定。

### recommended_exams

- 自增主键
- `session_id`
- 检查名称、优先级、触发原因、来源、规则版本和注意事项
- `created_at`

### intake_reports

- `id`：兼容现有接口的 `record_id`，作为报告主键
- `session_id`：唯一外键
- `patient_id`
- `completion_status`
- `report_markdown`
- `rule_version`
- `created_at`、`updated_at`

### audit_events

- 自增主键
- `session_id`
- `event_type`
- `turn`
- `field_key`
- `payload_json`
- `rule_version`
- `created_at`

### doctor_reviews

- 自增主键
- `report_id`
- `doctor_id`
- `status`
- `review_note`
- `created_at`、`updated_at`

本次只创建表和模型，不接入前端医生审核操作。

## Repository 接口

提供以下核心能力：

- 创建或获取患者
- 创建、读取和更新问诊会话
- 在一次事务中保存会话快照、字段状态、新问答和审计事件
- 保存基础测量
- 保存或替换推荐检查
- 创建或更新最终报告
- 按患者列出历史报告
- 按患者和记录 ID 读取历史详情
- 按会话查找已有报告，保证自动保存幂等

Repository 对外继续返回现有业务层使用的字典结构，减少领域逻辑改动。

## 状态恢复

服务收到会话请求时：

1. 从 MySQL 查询会话。
2. 如果不存在，则创建初始会话和字段状态。
3. 将关系表组装为现有内部状态字典。
4. 执行当前规则版本下的状态规范化。
5. 如规范化改变状态，则在同一事务中写回。

后端进程不再以全局内存字典作为事实来源。可保留短生命周期缓存，但数据库始终是唯一事实来源。

## 事务与并发

- 基础资料提交、开放回答、追问回答、分析结果应用和最终归档分别使用独立事务。
- 追问回答与字段状态更新必须原子提交。
- 更新会话时校验 `version`；版本不一致返回冲突错误，客户端重新获取状态。
- 最终报告按 `session_id` 唯一，重复保存执行更新或返回现有记录。
- 历史详情始终按 `patient_id + record_id` 查询，禁止患者读取他人报告。

## API 兼容性

现有前端 API 路径和主要响应结构保持不变，包括：

- `/api/intake/session/{session_id}`
- `/baseline`
- `/open-answer`
- `/analyze`
- `/follow-up`
- `/doctor-summary`
- `/api/save_record`
- `/api/patient/records`

前端无需在第一阶段同步重构。

## JSON 数据迁移

提供一次性命令，将 `backend/records/*.json` 导入 MySQL：

- 根据 `record_id` 和 `session_id` 去重
- 缺少 `patient_id` 的旧记录归入 `demo-zhang`
- 保留原始创建时间、报告、追问回答、推荐检查和 BMI 信息
- 无法映射的旧字段写入审计事件的迁移载荷，不静默丢弃
- 支持 `--dry-run` 输出导入数量和错误，不写数据库

迁移完成后不自动删除原 JSON 文件。

## 配置与启动

- `.env.example` 增加 `DATABASE_URL`
- 应用启动时检查数据库连接和迁移版本
- 数据库不可用时健康检查返回失败
- 不静默回退到 JSON 或内存模式
- README 增加建库、迁移、启动和旧数据导入步骤

## 错误处理

- 数据库连接失败：服务启动失败并输出不含密码的错误信息
- 并发版本冲突：返回 HTTP 409
- 会话不存在或不属于当前患者：返回 HTTP 404
- 事务失败：整体回滚，不留下部分问答或部分字段状态
- 旧数据格式错误：迁移脚本记录文件名和原因，继续处理其他文件

## 测试策略

- 保留现有153项后端测试和33项前端测试。
- 为 ORM 模型、Repository CRUD、事务回滚、患者隔离和幂等保存增加测试。
- 为服务重启后的会话恢复增加集成测试。
- 为 JSON 迁移的正常、重复、缺字段和错误文件场景增加测试。
- MySQL 集成测试单独运行，不依赖开发者日常单元测试环境。

## 验收标准

- 后端重启后可继续未完成问诊。
- 所有问答、字段状态和停止原因均能从数据库恢复。
- 同一会话重复保存不会生成重复档案。
- 不同患者无法读取彼此档案。
- 事务失败不会产生半条问答记录。
- 旧 JSON 档案可重复执行迁移且不会重复导入。
- 现有前后端测试继续全部通过。
- 新增持久化测试全部通过。
