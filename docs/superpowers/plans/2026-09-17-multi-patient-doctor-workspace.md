# Multi-Patient Doctor Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有单患者混合页面改造成多患者患者端与独立医生只读工作台，并展示追问与停止决策解释。

**Architecture:** 后端以 `patient_id` 作为所有会话和档案访问的显式边界，新增患者目录、医生聚合查询及可重复迁移。前端由入口分流组件选择身份，再分别渲染患者工作区或医生工作区；医生端不复用患者输入界面。

**Tech Stack:** Python 3.11+、FastAPI、SQLAlchemy 2、Alembic、MySQL 8、Vue 3、Vite、Node Test Runner、Python unittest

## Global Constraints

- 第一版为演示身份系统，必须展示“演示环境”。
- 患者端只能访问路径中 `patient_id` 对应的数据。
- 医生端第一版只读。
- 迁移不得删除任何会话、档案、回答、字段状态、检查建议或审计记录。
- 旧 API 暂时保留兼容，现有前端迁移完成后不再调用。
- 医生决策解释由后端生成，前端不得重新计算规则。

---

### Task 1: 患者目录与多患者仓储能力

**Files:**
- Modify: `backend/repository.py`
- Create: `backend/patient_directory.py`
- Create: `backend/tests/test_patient_directory.py`
- Modify: `backend/tests/test_repository.py`

**Interfaces:**
- Produces: `DEMO_PATIENTS: tuple[dict, ...]`
- Produces: `seed_demo_patients(repository) -> list[dict]`
- Produces: `SqlAlchemyIntakeRepository.list_patients() -> list[dict]`
- Produces: `SqlAlchemyIntakeRepository.get_patient(patient_id: str) -> dict | None`
- Produces: `SqlAlchemyIntakeRepository.list_patient_sessions(patient_id: str) -> list[dict]`

- [ ] **Step 1: Write failing patient-directory tests**

```python
def test_demo_patient_seed_is_idempotent(self):
    first = seed_demo_patients(self.repository)
    second = seed_demo_patients(self.repository)
    self.assertEqual([item["patient_id"] for item in first], ["patient-zhang", "patient-ma", "patient-li", "unassigned"])
    self.assertEqual(len(self.repository.list_patients()), 4)
    self.assertEqual(first, second)

def test_patient_session_listing_never_crosses_patient_boundary(self):
    self.repository.get_or_create_session("zhang-session", "patient-zhang")
    self.repository.get_or_create_session("ma-session", "patient-ma")
    self.assertEqual(
        [item["session_id"] for item in self.repository.list_patient_sessions("patient-zhang")],
        ["zhang-session"],
    )
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_patient_directory tests.test_repository -v`

Expected: FAIL because the directory and repository methods do not exist.

- [ ] **Step 3: Implement the patient directory**

```python
DEMO_PATIENTS = (
    {"patient_id": "patient-zhang", "display_name": "张女士"},
    {"patient_id": "patient-ma", "display_name": "马先生"},
    {"patient_id": "patient-li", "display_name": "李女士"},
    {"patient_id": "unassigned", "display_name": "未归属患者"},
)

def seed_demo_patients(repository):
    return [repository.ensure_patient(item["patient_id"], item["display_name"]) for item in DEMO_PATIENTS]
```

在 repository 中实现 `ensure_patient`、`list_patients`、`get_patient` 和 `list_patient_sessions`，返回序列化字典，不向调用方暴露 ORM 实例。

- [ ] **Step 4: Verify Task 1**

Run: `python -m unittest tests.test_patient_directory tests.test_repository -v`

Expected: PASS.

---

### Task 2: 历史数据患者归属迁移

**Files:**
- Create: `backend/scripts/migrate_patient_ownership.py`
- Create: `backend/tests/test_patient_ownership_migration.py`

**Interfaces:**
- Consumes: `DEMO_PATIENTS`
- Produces: `patient_id_for_name(name: str | None) -> str`
- Produces: `migrate_patient_ownership(repository, dry_run: bool = False) -> MigrationSummary`

- [ ] **Step 1: Write failing migration tests**

```python
def test_name_mapping(self):
    self.assertEqual(patient_id_for_name("张女士"), "patient-zhang")
    self.assertEqual(patient_id_for_name("马先生"), "patient-ma")
    self.assertEqual(patient_id_for_name("李女士"), "patient-li")
    self.assertEqual(patient_id_for_name("匿名患者"), "unassigned")

def test_migration_moves_report_and_session_together_and_is_idempotent(self):
    result = migrate_patient_ownership(self.repository)
    again = migrate_patient_ownership(self.repository)
    self.assertEqual(result.updated_reports, 1)
    self.assertEqual(again.updated_reports, 0)
    self.assertIsNotNone(self.repository.get_patient_report("patient-zhang", "record-a"))
    self.assertEqual(self.repository.get_or_create_session("session-a", "patient-zhang")["patient_id"], "patient-zhang")
```

- [ ] **Step 2: Run test and verify failure**

Run: `python -m unittest tests.test_patient_ownership_migration -v`

Expected: FAIL because the migration module does not exist.

- [ ] **Step 3: Implement dry-run and idempotent migration**

The script must update `intake_sessions.patient_id`, `intake_reports.patient_id`, their JSON snapshots, and ensure the target patient row exists in one transaction per ownership group. `--dry-run` must only count proposed changes.

- [ ] **Step 4: Verify Task 2**

Run: `python -m unittest tests.test_patient_ownership_migration -v`

Expected: PASS.

---

### Task 3: Patient-scoped and doctor read-only APIs

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/intake_flow.py`
- Create: `backend/doctor_workspace.py`
- Create: `backend/tests/test_multi_patient_api.py`
- Create: `backend/tests/test_doctor_workspace.py`

**Interfaces:**
- Produces: `create_intake_session(patient_id: str, session_id: str) -> dict`
- Produces: `build_doctor_patient_list(repository) -> list[dict]`
- Produces: `build_doctor_patient_detail(repository, patient_id: str) -> dict`
- Produces the patient and doctor routes specified in the design document.

- [ ] **Step 1: Write failing API boundary tests**

```python
async def test_patient_cannot_read_another_patients_record(self):
    response = await main.get_scoped_patient_record("patient-ma", "zhang-record")
    self.fail("expected HTTPException")

async def test_doctor_patient_list_contains_aggregate_status(self):
    items = await main.list_doctor_patients()
    zhang = next(item for item in items if item["patient_id"] == "patient-zhang")
    self.assertIn("record_count", zhang)
    self.assertIn("latest_intake_at", zhang)
    self.assertIn("has_safety_alert", zhang)
```

The cross-patient test must assert HTTP 404 using `assertRaises(HTTPException)` and verify no record payload is returned.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_multi_patient_api tests.test_doctor_workspace -v`

Expected: FAIL because scoped routes and doctor builders do not exist.

- [ ] **Step 3: Implement patient-scoped routes**

Add `patient_id` to session creation and every patient record/session route. Before reading or mutating a session, load it through the repository using the same patient ID. Return 404 for unknown patients and cross-patient resources.

- [ ] **Step 4: Implement doctor aggregation routes**

Return patient list items with `patient_id`, `display_name`, `record_count`, `unfinished_count`, `latest_intake_at`, `latest_phase`, and `has_safety_alert`. Patient detail returns baseline summary and ordered session summaries. Session summary returns `build_doctor_summary(...)` plus decision explanation from Task 4.

- [ ] **Step 5: Verify Task 3**

Run: `python -m unittest tests.test_multi_patient_api tests.test_doctor_workspace -v`

Expected: PASS.

---

### Task 4: 决策解释生成器

**Files:**
- Modify: `backend/intake_views.py`
- Create: `backend/decision_explanation.py`
- Create: `backend/tests/test_decision_explanation.py`
- Modify: `backend/tests/test_intake_views.py`

**Interfaces:**
- Produces: `build_decision_explanation(state: dict) -> dict`
- Extends: `build_doctor_summary(state)["decision_explanation"]`

- [ ] **Step 1: Write failing explanation tests**

```python
def test_continuing_state_explains_selected_field(self):
    explanation = build_decision_explanation(self.follow_up_state)
    self.assertEqual(explanation["status"], "continue")
    self.assertEqual(explanation["selected_field"]["key"], self.follow_up_state["current_field_key"])
    self.assertGreater(explanation["core_total"], explanation["core_completed"])

def test_terminal_state_explains_stop_and_timeline(self):
    explanation = build_decision_explanation(self.completed_state)
    self.assertTrue(explanation["stop"]["should_stop"])
    self.assertTrue(explanation["stop"]["reason"])
    self.assertIsInstance(explanation["timeline"], list)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_decision_explanation tests.test_intake_views -v`

Expected: FAIL because the explanation builder does not exist.

- [ ] **Step 3: Implement deterministic explanation output**

Use field definitions, `field_states`, `blocking_keys`, `current_field_key`, `attempt_number`, `stop_reason`, and `audit`. Translate internal reason codes to doctor-facing Chinese in the backend. Do not call an LLM.

- [ ] **Step 4: Verify Task 4**

Run: `python -m unittest tests.test_decision_explanation tests.test_intake_views -v`

Expected: PASS.

---

### Task 5: 前端入口分流与患者身份切换

**Files:**
- Create: `frontend/src/patient-context.js`
- Create: `frontend/src/api.js`
- Create: `frontend/src/components/IdentityChooser.vue`
- Create: `frontend/src/components/PatientWorkspace.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Create: `frontend/tests/patient-context.test.mjs`
- Modify: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Produces: `readPatientId(search: string) -> string`
- Produces: `patientUrl(patientId: string) -> string`
- Produces: `doctorUrl() -> string`
- Produces: `request(path: string, options?: RequestInit) -> Promise<any>`
- `PatientWorkspace` prop: `patientId: string`

- [ ] **Step 1: Write failing routing and isolation tests**

```js
test('root without identity renders chooser', () => {
  assert.match(appSource, /<IdentityChooser v-if="!patientId && !doctorMode"/)
})

test('patient URLs preserve explicit patient identity', () => {
  assert.equal(readPatientId('?patient=patient-ma'), 'patient-ma')
  assert.equal(patientUrl('patient-li'), '/?patient=patient-li')
})

test('doctor mode never renders PatientWorkspace', () => {
  assert.match(appSource, /<DoctorWorkspace v-if="doctorMode"/)
  assert.match(appSource, /<PatientWorkspace v-else-if="patientId"/)
})
```

- [ ] **Step 2: Run tests and verify failure**

Run: `npm.cmd test -- --test-name-pattern="identity|patient URLs|doctor mode"`

Expected: FAIL because routing helpers and split workspaces do not exist.

- [ ] **Step 3: Extract the current patient UI**

Move the existing patient template/state/request flow from `App.vue` to `PatientWorkspace.vue`. Replace all old patient history/session URLs with `/api/patients/${patientId}/...`. Replace hard-coded “张女士” with the selected patient response. Keep existing patient tests passing.

- [ ] **Step 4: Implement identity chooser and quick switcher**

`IdentityChooser` loads `/api/patients`, shows the three named demo patients plus “进入医生工作台”, and displays “演示环境”. Patient sidebar switcher navigates to `patientUrl(selectedId)` and must not carry the previous session query parameter.

- [ ] **Step 5: Verify Task 5**

Run: `npm.cmd test`

Expected: all frontend tests PASS.

---

### Task 6: 独立医生三栏工作台

**Files:**
- Create: `frontend/src/components/DoctorWorkspace.vue`
- Create: `frontend/src/components/DoctorPatientList.vue`
- Create: `frontend/src/components/DoctorPatientDetail.vue`
- Create: `frontend/src/components/DecisionExplanationPanel.vue`
- Modify: `frontend/src/components/DoctorExecutionPanel.vue`
- Modify: `frontend/src/style.css`
- Create: `frontend/tests/doctor-workspace.test.mjs`

**Interfaces:**
- `DoctorPatientList` props: `patients: Array`, `selectedPatientId: string`
- `DoctorPatientList` emits: `select(patientId: string)`
- `DoctorPatientDetail` props: `patient: Object`, `sessions: Array`, `selectedSessionId: string`
- `DoctorPatientDetail` emits: `select-session(sessionId: string)`
- `DecisionExplanationPanel` prop: `explanation: Object`

- [ ] **Step 1: Write failing doctor-workspace tests**

```js
test('doctor workspace is read-only and has three semantic columns', () => {
  assert.match(source, /class="doctor-patient-column"/)
  assert.match(source, /class="doctor-detail-column"/)
  assert.match(source, /class="doctor-decision-column"/)
  assert.doesNotMatch(source, /textarea/)
  assert.doesNotMatch(source, /开始整理/)
})
```

- [ ] **Step 2: Run test and verify failure**

Run: `npm.cmd test -- --test-name-pattern="doctor workspace"`

Expected: FAIL because the independent workspace does not exist.

- [ ] **Step 3: Implement three-column data flow**

On mount load `/api/doctor/patients`; select the first patient; load its detail and sessions; select its latest session; load `/api/doctor/sessions/{session_id}/summary`. Switching patient resets the selected session before loading the new detail.

- [ ] **Step 4: Implement read-only UI and responsive layout**

Desktop uses `grid-template-columns: 260px minmax(420px, 1fr) minmax(320px, .72fr)`. At `max-width: 1100px`, use one column in the order patient list, detail, explanation. No doctor component contains patient submission actions.

- [ ] **Step 5: Verify Task 6**

Run: `npm.cmd test`

Expected: all frontend tests PASS.

---

### Task 7: 全量迁移、回归与浏览器验收

**Files:**
- Modify: `README.md`
- Modify: `.gitignore` if present; otherwise Create: `.gitignore`

**Interfaces:**
- Documents patient and doctor URLs, migration preview/apply commands, and demo-only identity limitation.

- [ ] **Step 1: Run backend full suite**

Run: `python -m unittest discover -s tests -v`

Expected: 0 failures.

- [ ] **Step 2: Run frontend full suite and build**

Run: `npm.cmd test`

Expected: 0 failures.

Run: `npm.cmd run build`

Expected: Vite build exits with code 0.

- [ ] **Step 3: Preview and apply migration**

Run: `python -m scripts.migrate_patient_ownership --dry-run`

Expected: prints patient ownership changes without database writes.

Run: `python -m scripts.migrate_patient_ownership`

Expected: creates demo patients, migrates records and sessions, and exits 0.

- [ ] **Step 4: Browser acceptance**

Verify `/`, each patient URL, and `/?view=doctor` at desktop width and 390px mobile width. Confirm histories differ between patients, doctor switching changes detail, doctor view has no input box, and cross-patient record URLs return 404.

- [ ] **Step 5: Update documentation**

Rewrite README in UTF-8 Chinese with exact start commands, URLs, migration commands, demo identity warning, and test commands. Add `.gitignore` entries for `__pycache__/`, `*.pyc`, `*.log`, `.env`, `frontend/dist/`, and generated browser screenshots.

- [ ] **Step 6: Commit**

The current project is not a Git repository, so no commit is executed. Preserve all modified files for user review.
