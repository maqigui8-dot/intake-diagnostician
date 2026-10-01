# 多患者与独立医生工作台设计

## 1. 目标

彻底拆分患者端和医生端。患者端以明确的 `patient_id` 运行，只能查看自己的问诊；医生端成为独立的三栏只读工作台，可查看多个患者、历次问诊和完整度决策解释。

第一版为演示身份系统，不实现账号、密码和正式授权。页面必须明确标注“演示环境”。

## 2. 前端架构

`App.vue` 仅负责入口分流：

```text
App.vue
├── IdentityChooser
├── PatientWorkspace
└── DoctorWorkspace
```

访问方式：

```text
/                              身份选择页
/?patient=patient-zhang        张女士患者端
/?patient=patient-ma           马先生患者端
/?patient=patient-li           李女士患者端
/?view=doctor                  医生工作台
```

患者端侧栏底部提供演示患者切换器。切换后更新 URL、清空当前内存状态并重新加载该患者数据。医生端不渲染患者输入框、聊天输入区或患者操作。

公共能力拆分为患者身份解析、API 请求、日期格式化和问诊阶段格式化工具。

## 3. 患者数据

创建四个患者：

| patient_id | name | 用途 |
| --- | --- | --- |
| `patient-zhang` | 张女士 | 演示患者 |
| `patient-ma` | 马先生 | 演示患者 |
| `patient-li` | 李女士 | 演示患者 |
| `unassigned` | 未归属患者 | 承接无法识别的历史档案 |

会话和档案继续通过 `patient_id` 外键归属患者。新会话必须显式提供患者 ID，不再使用 `demo-zhang` 默认值。

## 4. 数据迁移

新增一次性、可重复执行的迁移脚本：

- 根据现有档案的 `patient_name` 将含“张”“马”“李”的记录分别迁移。
- 匿名、空姓名或无法识别的记录迁移到 `unassigned`。
- 对档案对应的会话同步更新 `patient_id`。
- 不删除档案、回答、字段状态、检查建议和审计记录。
- 支持 `--dry-run` 预览。
- 再次执行不产生重复患者或重复数据。

## 5. API

患者端：

```text
GET  /api/patients
POST /api/patients/{patient_id}/sessions
GET  /api/patients/{patient_id}/sessions/{session_id}
GET  /api/patients/{patient_id}/sessions/unfinished
POST /api/patients/{patient_id}/sessions/{session_id}/archive
GET  /api/patients/{patient_id}/records
GET  /api/patients/{patient_id}/records/{record_id}
POST /api/patients/{patient_id}/records/{record_id}/delete
```

所有患者接口校验目标资源属于路径中的 `patient_id`。旧接口在过渡期保留兼容，但前端不再调用。

医生端只读接口：

```text
GET /api/doctor/patients
GET /api/doctor/patients/{patient_id}
GET /api/doctor/patients/{patient_id}/sessions
GET /api/doctor/sessions/{session_id}/summary
```

## 6. 医生工作台

桌面端三栏布局：

- 左栏：患者列表。展示姓名、最近问诊时间、问诊数量和危险信号状态。
- 中栏：所选患者资料与历次问诊。展示基础资料、问答记录、诊前档案。
- 右栏：决策解释。展示核心字段完成数量、关键缺口、当前/最后一项追问的来源、停止原因、冲突、危险信号和检查建议。

医生端第一版只读，不提供修改、确认、删除和归档操作。

移动端按“患者列表 → 问诊详情 → 决策解释”单列排列，不保留强制三栏。

## 7. 决策解释数据

医生摘要新增：

```json
{
  "decision_explanation": {
    "status": "continue",
    "core_completed": 7,
    "core_total": 9,
    "blocking_fields": [],
    "selected_field": {
      "key": "medication",
      "label": "当前用药情况",
      "status": "not_asked",
      "priority": 2,
      "attempts": 0,
      "reason": "尚未确认的高优先级安全字段"
    },
    "stop": {
      "should_stop": false,
      "reason": "核心信息尚未完整"
    },
    "timeline": []
  }
}
```

后端生成解释，前端只负责展示，不在前端重新计算规则。

## 8. 错误与空状态

- 无患者参数时显示身份选择，不自动假设张女士。
- 患者不存在时返回 404，并提供返回身份选择入口。
- 患者没有问诊时显示明确空状态。
- 医生工作台没有数据时仍显示患者列表和空详情提示。
- 数据库不可用时显示服务错误，不回退到混合身份或 JSON 存储。

## 9. 测试

- repository：患者创建、资源归属、跨患者拒绝。
- migration：姓名映射、未归属、幂等、会话同步。
- API：患者列表、患者专用接口、医生只读接口、404 和跨患者访问。
- frontend：入口分流、患者切换、医生端不包含输入框、三栏数据绑定。
- browser：三位患者数据隔离、医生切换患者、桌面与 390px 移动端布局。

## 10. 实施顺序

1. 多患者种子数据与迁移脚本。
2. 患者专用 API 和医生只读 API。
3. 前端入口分流与身份选择。
4. 抽取现有患者工作区。
5. 实现医生三栏工作台。
6. 增加决策解释。
7. 完整回归和浏览器验收。
