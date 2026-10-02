# 🍂 小郎中问诊 · 成人肥胖中医诊前问诊系统

一个基于 AI 的中医诊前问诊系统。患者通过自然语言描述不适，系统按照中医"十问歌"与《肥胖症诊疗指南（2024 年版）》逐步采集诊前资料，生成可由患者核对的结构化档案，供后续就医时参考。

> 定位：只负责采集、整理、计算与提示，**不诊断、不开方**，最终结论由医生确认。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic |
| 数据库 | MySQL 8（PyMySQL 驱动，本地免安装版） |
| 前端 | Vue 3 + Vite + TailwindCSS |
| 智能体框架 | Deep Agents（LangChain / LangGraph） |
| LLM | DeepSeek API（deepseek-v4-flash）或本地 Ollama（qwen3:8b） |

## 核心设计

**确定性规则与大模型分工**：字段采集顺序、阈值判断、完整度计算全部由规则代码管理；大模型只负责从患者自由表达中提取字段证据、改写追问话术，不做任何医学判断。

### 问诊字段

全部字段集中定义在 `backend/obesity_intake_schema.py`（`adult-obesity-intake-v1` 规则版本），共 30+ 个字段，分三组：

- **辨证资料（differentiation）**：肥胖情况、起病经过、中医症状（食欲/寒热/二便/舌象等）、生活方式、近期检查
- **安全资料（safety）**：过敏史、当前用药、既往疾病、妊娠情况、危险信号（硬性必答）
- 每个字段带：权重（1~7）、优先级、是否硬性必答、最多追问次数、初始提问与追问话术

### 诊前资料就绪度与分层资料覆盖度

内部的分层资料覆盖度按权重计算：`confirmed` 得满分、`partial` 得一半、`not_asked` / `unavailable` 得零分。旧版阈值规则仍保留在代码中供历史记录和规则核对使用；当前产品不开放医生工作台：

| 层 | 内容 | 及格线 |
|---|---|---|
| 风险层 | 肥胖史、家族史、化验检查、生活方式 | ≥ 80% |
| 中医层 | 十问歌相关症状 | ≥ 70% |
| 安全层 | 过敏、用药、既往疾病、危险信号 | 必须 100% |

当前在线追问以 `evaluate_patient_readiness` 的核心资料就绪判定为准。以下情况会阻塞正常完成：

- 基础资料（身高体重）未确认
- 当前患者适用的核心字段未确认
- 核心字段存在未解决的矛盾

核心字段由 `PATIENT_CORE_FIELD_KEYS` 定义；妊娠相关字段按患者情况决定是否适用，因此分母可能不同。患者端显示关键资料已确认数与剩余数，方便理解追问进度。分层百分比仅用于内部分析扩展资料覆盖情况，不单独决定是否结束追问。

## 项目结构

```
intake-diagnostician/
├── backend/
│   ├── main.py                    # FastAPI 应用与 API 路由
│   ├── agent.py                   # Deep Agents 问诊智能体 + 会话管理
│   ├── obesity_intake_schema.py   # 问诊字段定义（权重/优先级/话术）
│   ├── intake_execution.py        # 完整度计算与阈值判定
│   ├── intake_flow.py             # 问诊流程编排
│   ├── intake_question_policy.py  # 提问顺序与追问策略
│   ├── follow_up_policy.py        # 追问策略
│   ├── obesity_diagnosis.py       # 诊断参考计算（BMI 等，供医生参考）
│   ├── decision_explanation.py    # 决策解释生成
│   ├── exam_recommendations.py    # 检查建议
│   ├── skill_analysis.py          # 技能/证型分析
│   ├── models.py                  # MySQL 数据模型（患者/会话/字段状态/报告等 9 张表）
│   ├── repository.py              # 会话与档案持久化（SQLAlchemy）
│   ├── db.py                      # 数据库连接
│   ├── migrations/                # Alembic 数据库迁移
│   ├── scripts/                   # JSON 档案导入、患者归属迁移脚本
│   ├── records/                   # 历史演示档案（JSON）
│   └── tests/                     # 后端测试（20 个测试文件）
├── frontend/
│   └── src/
│       ├── App.vue / RootApp.vue  # 主布局与路由分发
│       ├── components/
│       │   ├── IdentityChooser.vue       # 演示患者选择页
│       │   ├── ChatWindow.vue            # 患者问诊对话核心组件
│       └── api.js                 # 前端 API 封装
├── start-mysql.ps1                # 本地 MySQL 启动脚本
└── .env.example                   # 环境变量示例
```

## 快速启动

### 1. 本地 MySQL

本机使用 MySQL Community Server 8.4.11 LTS 免管理员 ZIP 版：

```text
C:\Users\Administrator\Desktop\project\mysql-8.4.11-winx64
```

重启电脑后先运行项目根目录下的启动脚本（已检测 3306 端口，重复执行安全）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-mysql.ps1
```

首次使用需初始化数据库与账号：

```sql
CREATE DATABASE intake_diagnostician CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'intake_user'@'localhost' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON intake_diagnostician.* TO 'intake_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 后端

```powershell
cd backend
pip install -r requirements.txt

# 配置环境变量（复制根目录 .env.example 到 backend/.env 并填写数据库密码）
Copy-Item ..\.env.example .env

# 创建数据库结构
python -m alembic upgrade head

# 启动后端服务（端口 8000）
uvicorn main:app --port 8000 --reload
```

在 `backend/.env` 中配置：

```dotenv
DATABASE_URL=mysql+pymysql://intake_user:change_me@127.0.0.1:3306/intake_diagnostician?charset=utf8mb4
DEEPSEEK_API_KEY=
```

**数据持久化说明**：问诊会话、字段状态、追问回答、四诊报告等均通过 `repository.py` 持久化到 MySQL；应用启动时检查数据库连接，数据库不可用时服务拒绝启动。启动时会自动播种演示患者（张女士、马先生、李女士）。

### 导入旧 JSON 档案（可选）

```powershell
# 预览，不写数据库
python -m scripts.migrate_json_records --records-dir records --dry-run

# 确认后正式导入（按 record_id 和 session_id 幂等去重）
python -m scripts.migrate_json_records --records-dir records

# 多患者归属迁移（同样支持 --dry-run 预览）
python -m dotenv run -- python -m scripts.migrate_patient_ownership --dry-run
```

### 3. 前端

```powershell
cd frontend
npm install
npm run dev
```

### 4. 访问

浏览器打开 `http://localhost:5173`，先进入演示患者选择页。

| 页面 | 地址 |
|---|---|
| 演示患者选择 | `http://localhost:5173/` |
| 张女士患者端 | `http://localhost:5173/?patient=patient-zhang` |
| 马先生患者端 | `http://localhost:5173/?patient=patient-ma` |
| 李女士患者端 | `http://localhost:5173/?patient=patient-li` |

当前患者选择仅用于项目演示，不是正式的登录或鉴权系统。URL 中的 `patient_id` 可被修改，不可用于真实患者资料；若用于真实场景，必须先接入账号认证与权限控制。

## 使用流程

1. 患者端先确认基础资料（身高体重），随后用自然语言描述不适
2. 系统优先核对安全信息，再按字段规则逐项追问；回答不清时最多再确认一次
3. 对当前问题的明确回答（包括能对应问题的“没有”和明确时长）不再换种说法追问；同一字段至多询问两次，问不到时继续采集其他可问字段
4. 核心字段确认齐且没有未解决的矛盾后，显示保存前核对区；患者可以修正主诉、病程、过敏、用药、既往病史，原问答与修订记录保留
5. 若在线追问已停止但核心字段仍有缺口，会话保留为可从侧栏恢复的未完成草稿，展示具体缺口并允许患者自行补充；草稿不能保存为正式档案，也不承诺系统会在诊中核实
6. 患者核对完成后主动点击“确认并保存档案”；未保存的完成会话可从侧栏继续核对
7. 患者端查看问答记录和结构化诊前档案；结果仅用于资料整理及就医准备，不作为独立诊断

## LLM 配置说明

后端启动时按优先级选择模型（见 `backend/agent.py` 的 `build_llm`）。请求失败时会使用本地规则处理本轮资料；不会在一次失败后自动切换到表中的下一个云端模型：

| 优先级 | 场景 | 环境变量 | 模型 |
|------|------|----------|------|
| 1 | 校内千问（校园网内，免费） | `SCHOOL_LLM_API_KEY=sk-xxx` | `vllm.Qwen3.8-27B`（可用 `SCHOOL_LLM_MODEL` / `SCHOOL_LLM_BASE_URL` 覆盖） |
| 2 | DeepSeek 云端 | `DEEPSEEK_API_KEY=xxx` | deepseek-v4-flash |
| 3 | 本地 Ollama | 前两者都未配置 | qwen3:8b |

校内网关为 OpenAI 兼容接口，仅 `POST /api/chat/completions` 可用（`/v1/*` 不可用）；
校内 IP 不可走系统代理，后端已用 `httpx.Client(trust_env=False)` 强制直连。
`vllm.Qwen3.8-27B` 为推理模型，思考过程单独返回 `reasoning_content`，正文在 `content`；
`max_tokens` 需留足思考空间（当前配置 4096）。

使用本地 Ollama 时，请确保：

```bash
ollama pull qwen3:8b
ollama serve
```

## API 概览

主要接口（完整列表见 `backend/main.py`，或启动后访问 `http://localhost:8000/docs`）：

| 分组 | 接口 |
|---|---|
| 患者与会话 | `GET /api/patients`、`POST /api/patients/{id}/sessions`、`GET .../sessions/unfinished` |
| 问诊流程 | `POST .../baseline`（基础资料）、`POST .../open-answer`（自由表达）、`POST .../follow-up`（字段追问）、`POST .../analyze`（分析）、`POST .../corrections`（患者修订）、`POST .../save`（确认保存）、`POST .../archive`（归档） |
| 患者档案 | `GET /api/patients/{id}/records`、`GET .../records/{record_id}`、`POST .../records/{record_id}/delete` |
| 健康检查 | `GET /api/health` |

旧版匿名 `/api/chat`、`/api/intake/session/...`、`/api/records`、`/api/save_record` 已不再注册为公开路由；内部兼容函数暂时保留，用于历史测试和过渡。

## 测试

```powershell
cd backend
python -m unittest discover -s tests -v

cd ..\frontend
npm.cmd test
npm.cmd run build
```

固定离线评测包含 42 个合成的单轮回答与停止判断场景（含病程时长的否定、含糊反例），以及 30 组由六种主诉和五类安全/用药变化组合而成的多轮会话；两者均不调用线上模型：

```powershell
cd backend
python -m evaluation.runner
python -m evaluation.dialogues
```

前者输出按类型统计与失败病例 ID；后者输出每组终止状态、轮数、是否超出同一字段追问上限，以及合成危险信号的检出率。两套病例均为固定合成样本，结果只衡量离线规则回退流程，不代表真实患者或线上 LLM 的准确率，也不是临床有效性验证。

## 已知待办

- [ ] 组会演示材料（presentations/）与文档同步到当前架构
- [ ] 正式接入账号认证与权限控制（当前仅演示级身份选择）
- [ ] DeepSeek 偶发响应超时（>45 秒）的降级策略优化
